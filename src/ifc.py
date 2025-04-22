import re
import rdflib
import pathlib
import ifcopenshell

from src.config import AppConfig


def to_uri(s: str):
    return rdflib.URIRef(re.sub(r'[^a-z0-9]', '', s, flags=re.IGNORECASE))


def getElements(ifcFile, ifcType: str):
    return ifcFile.by_type(ifcType)


def getIfcAttribute(ifcElement, attribute):
    """
    Fetches non-empty attributes (if they exist).
    """
    try:
        return getattr(ifcElement, attribute)
    except AttributeError:
        pass


def getSpatialParent(ifcElement):
    """Fetch the first spatial parent element."""
    parent = getIfcAttribute(ifcElement, 'ContainedInStructure')
    if parent:
        return parent[0].RelatingStructure


def checkIfcElementType(ifcElement, ifcType):
    """Checks for matching IFC element types."""
    if getIfcAttribute(ifcElement, 'is_a'):
        return ifcElement.is_a() == ifcType


def getHierarchicalParent(ifcElement):
    """Fetch the first structural parent element."""

    parent = getIfcAttribute(ifcElement, 'Decomposes')
    if parent:
        return parent[0].RelatingObject

    parent = getIfcAttribute(ifcElement, 'VoidsElements')
    if parent:
        return parent[0].RelatingBuildingElement


def getHierarchicalChildren(ifcElement):
    """Fetch the child elements from the first structural aggregation."""
    children = getIfcAttribute(ifcElement, 'IsDecomposedBy')
    if children:
        return children[0].RelatedObjects
    # ... try again for voids:
    children = getIfcAttribute(ifcElement, 'HasOpenings')
    if children:
        # just get the voids, not the relations
        return [i.RelatedOpeningElement for i in children]


def getBuilding(ifcElement):
    """Find the building for this element."""

    if ifcElement:
        # direct spatial child elements in space
        parent = getSpatialParent(ifcElement)
        if checkIfcElementType(parent, 'IfcBuilding'):
            return parent
        else:
            # hierachically nested building elements
            parent = getHierarchicalParent(ifcElement)
            if checkIfcElementType(parent, 'IfcBuilding'):
                return parent
            else:
                return getSpace(parent)


def getStorey(ifcElement):
    """Find the building storey for this element."""

    if ifcElement:
        # direct spatial child elements in space or storey
        parent = getSpatialParent(ifcElement)
        if checkIfcElementType(parent, 'IfcBuildingStorey'):
            return parent
        elif checkIfcElementType(parent, 'IfcSpace'):
            return getStorey(parent)
        else:
            # hierachically nested building elements
            parent = getHierarchicalParent(ifcElement)
            if checkIfcElementType(parent, 'IfcBuildingStorey'):
                return parent
            else:
                return getStorey(parent)


def getSpace(ifcElement):
    """Find the space for this element."""

    if ifcElement:
        # direct spatial child elements in space
        parent = getSpatialParent(ifcElement)
        if checkIfcElementType(parent, 'IfcSpace'):
            return parent
        else:
            # hierachically nested building elements
            parent = getHierarchicalParent(ifcElement)
            if checkIfcElementType(parent, 'IfcSpace'):
                return parent
            else:
                return getSpace(parent)


def extract_topology(ifc_file_path: str | pathlib.Path):
    ifc_file = ifcopenshell.open(ifc_file_path)

    buildings = getElements(ifc_file, 'IFCBuilding')
    storeys = getElements(ifc_file, 'IFCBuildingStorey')
    spaces = getElements(ifc_file, 'IFCSpace')

    g = rdflib.Graph()
    REC = rdflib.Namespace('https://doc.realestatecore.io/4.0/#')
    design_ns = AppConfig.design_ns

    # Layout constants
    LEVEL_VERTICAL_SPACING = 100  # Vertical space between levels
    ROOM_HORIZONTAL_SPACING = 100  # Horizontal space between rooms
    ROOM_PER_ROW = 8  # Maximum number of rooms per row
    LEVEL_START_Y = 100  # Starting Y position for the first level
    START_X = 100  # Starting X position

    # Group spaces by storey
    spaces_by_storey = {}
    for space in spaces:
        storey = getStorey(space)
        if storey:
            storey_id = storey.GlobalId
            if storey_id not in spaces_by_storey:
                spaces_by_storey[storey_id] = []
            spaces_by_storey[storey_id].append(space)

    # Sort storeys by elevation (if available)
    sorted_storeys = sorted(storeys, key=lambda s: getattr(s, 'Elevation', 0) if hasattr(s, 'Elevation') else 0,
                            reverse=True)

    # Process buildings
    for building in buildings:
        uri = to_uri(building.GlobalId)
        g.add((uri, rdflib.RDF.type, REC.Building))
        g.add((uri, rdflib.RDFS.label, rdflib.Literal(building.Name)))

        # Add position for building
        position_node = rdflib.BNode()
        g.add((uri, design_ns.hasPosition, position_node))
        g.add((position_node, design_ns.x, rdflib.Literal(50)))  # Position buildings at left side
        g.add((position_node, design_ns.y, rdflib.Literal(50)))

    # Process storeys (levels)
    for level_index, storey in enumerate(sorted_storeys):
        uri = to_uri(storey.GlobalId)
        building_uri = to_uri(getBuilding(storey).GlobalId)

        g.add((uri, rdflib.RDF.type, REC.Level))
        g.add((uri, rdflib.RDFS.label, rdflib.Literal(storey.Name)))
        g.add((building_uri, rdflib.BRICK.hasLocation, uri))

        # Add position for level - stack them vertically
        level_y = LEVEL_START_Y + (level_index * LEVEL_VERTICAL_SPACING)
        position_node = rdflib.BNode()
        g.add((uri, design_ns.hasPosition, position_node))
        g.add((position_node, design_ns.x, rdflib.Literal(START_X)))
        g.add((position_node, design_ns.y, rdflib.Literal(level_y)))

        # Process rooms in this storey
        storey_spaces = spaces_by_storey.get(storey.GlobalId, [])

        # Sort spaces by name or ID for consistent layout
        storey_spaces.sort(key=lambda space: space.Name if hasattr(space, 'Name') else space.GlobalId)

        for room_index, space in enumerate(storey_spaces):

            uri = to_uri(space.GlobalId)
            storey_uri = to_uri(storey.GlobalId)

            g.add((uri, rdflib.RDF.type, REC.Room))
            g.add((uri, rdflib.RDFS.label, rdflib.Literal(space.Name)))
            g.add((storey_uri, rdflib.BRICK.hasLocation, uri))

            # Calculate room position in a grid layout within the level
            row = room_index // ROOM_PER_ROW
            col = room_index % ROOM_PER_ROW

            room_x = START_X + 200 + ROOM_HORIZONTAL_SPACING + (col * ROOM_HORIZONTAL_SPACING)
            room_y = level_y + (row * ROOM_HORIZONTAL_SPACING * 0.6)  # Use smaller vertical spacing for rooms

            position_node = rdflib.BNode()
            g.add((uri, design_ns.hasPosition, position_node))
            g.add((position_node, design_ns.x, rdflib.Literal(room_x)))
            g.add((position_node, design_ns.y, rdflib.Literal(room_y)))

    return g


if __name__ == '__main__':

    g = extract_topology('../data/IFC/boptest_multizone.ifc')

    g.serialize('../data/IFC/boptest_multizone.ttl')





