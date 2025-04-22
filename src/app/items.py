import math
import uuid
import rdflib

# PyQt imports
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsPolygonItem
from PyQt5.QtCore import Qt, QPointF, QByteArray
from PyQt5.QtGui import QPen, QBrush, QPainterPath, QPolygonF, QTransform
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem

# Local imports
from src.model import EntityLibrary, Point
from src.config import AppConfig


class EntityItem(QGraphicsSvgItem):
    """Graphical representation of an entity in the canvas."""

    def __init__(self, uri_ref: rdflib.URIRef | str):
        self.entity = EntityLibrary.find_entity_by_uri(uri_ref)

        # Generate a unique instance URI
        self.instance_uri = rdflib.URIRef(f"http://example.org/building/instances/{uuid.uuid4()}")
        self.label = ""
        self.external_references: list[dict] = []

        # Create SVG renderer
        self.renderer = QSvgRenderer(QByteArray(self.entity.svg_data.encode()))
        super().__init__()

        self.setSharedRenderer(self.renderer)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setZValue(1)
        self.setScale(1.0)

        # Track rotation
        self.rotation_angle = 0

        # Create connection port
        self.port = PortItem(self)
        self.port.setPos(*self.entity.port_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            return self._handle_position_change(value)

        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.port.update_connections()

        return super().itemChange(change, value)

    def _handle_position_change(self, new_pos):

        grid_size = AppConfig.grid_size
        point_line_y = AppConfig.get_point_line_height()

        # Get SVG dimensions
        svg_width = self.renderer.defaultSize().width()
        svg_height = self.renderer.defaultSize().height()

        # Calculate center offset
        center_x = svg_width / 2
        center_y = svg_height / 2

        # Snap to grid using center point
        x = round((new_pos.x() + center_x) / grid_size) * grid_size - center_x

        # Check if this is a Point entity and constrain to the line
        is_point = isinstance(self.entity, Point)
        if is_point:
            # For Point entities, Y coordinate is fixed to the line
            y = point_line_y - center_y
        else:
            # For other entities, use regular grid snapping
            y = round((new_pos.y() + center_y) / grid_size) * grid_size - center_y

        return QPointF(x, y)

    def apply_rotation(self, angle: float):
        """Apply rotation of specified angle around item's center."""

        self.rotation_angle = angle % 360

        # Get SVG center
        center_x = self.renderer.defaultSize().width() / 2
        center_y = self.renderer.defaultSize().height() / 2

        # Reset transform and apply rotation
        self.setTransform(QTransform())

        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.rotate(self.rotation_angle)
        transform.translate(-center_x, -center_y)

        self.setTransform(transform)
        self.port.update_connections()

        return self

    def rotate_90_degrees(self):
        """Rotate the entity by 90 degrees clockwise around its center."""

        self.apply_rotation((self.rotation_angle + 90) % 360)


class PortItem(QGraphicsEllipseItem):
    """Connection port attached to an entity that allows creating connections."""

    NORMAL_RADIUS = 4
    HOVER_RADIUS = 6

    DEFAULT_BRUSH = QBrush(Qt.gray)
    HOVER_BRUSH = QBrush(Qt.darkGray)

    def __init__(self, parent=None):
        super().__init__(-4, -4, 8, 8, parent)

        self.setAcceptHoverEvents(True)

        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)

        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(Qt.gray))
        self.setZValue(2)

        self.connections = []
        self.temp_connection = None
        self.entity_item = parent

        self._is_hovered = False

    def hoverEnterEvent(self, event):
        self.setHovered(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setHovered(False)
        super().hoverLeaveEvent(event)

    def setHovered(self, hovered: bool):
        """Set the visual state of the port based on hover status."""
        if self._is_hovered == hovered:
            return  # No change needed

        self._is_hovered = hovered
        if hovered:
            radius = self.HOVER_RADIUS
            self.setBrush(self.HOVER_BRUSH)  # Use hover brush
            self.setZValue(3)  # Bring hovered port slightly more forward if needed
        else:
            radius = self.NORMAL_RADIUS
            self.setBrush(self.DEFAULT_BRUSH)  # Use default brush
            self.setZValue(2)  # Reset Z value

        # Update the bounding rectangle to change size
        self.setRect(-radius, -radius, 2 * radius, 2 * radius)

    def scenePos(self):
        """Get the global scene position of the port."""
        return self.mapToScene(self.boundingRect().center())

    def add_connection(self, connection):
        """Register a connection with this port."""
        self.connections.append(connection)

    def remove_connection(self, connection):
        """Remove a connection from this port."""
        if connection in self.connections:
            self.connections.remove(connection)

    def update_connections(self):
        """Update positions of all connected connections."""
        for connection in self.connections:
            connection.update_position()


class JointItem(QGraphicsEllipseItem):
    """A movable joint on a connection line that provides routing control."""

    def __init__(self, parent=None):

        super().__init__(-4, -4, 8, 8, parent)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)

        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(Qt.black))
        self.setZValue(1.5)

        self.connection = parent

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            return self._snap_to_grid(value)
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            if self.connection:
                self.connection.update_position()

        return super().itemChange(change, value)

    def _snap_to_grid(self, new_pos):

        grid_size = AppConfig.grid_size

        # Snap to grid
        x = round(new_pos.x() / grid_size) * grid_size
        y = round(new_pos.y() / grid_size) * grid_size

        return QPointF(x, y)


class ConnectionItem(QGraphicsPathItem):
    """A connection between two ports with directional arrows and joints."""

    def __init__(
            self,
            source_port: PortItem,
            target_port: PortItem = None,
            relationship_type: rdflib.URIRef = None
    ):

        super().__init__()

        self.source_port = source_port
        self.target_port = target_port
        self.joints = []
        self.arrows = []

        self.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setZValue(0.5)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        # Register with ports
        if source_port:
            source_port.add_connection(self)
        if target_port:
            target_port.add_connection(self)

        # Create unique relationship URI
        self.instance_uri = AppConfig.building_ns[str(uuid.uuid4())]

        # Set default relationship type
        if relationship_type is None:
            self.relationship_type = rdflib.BRICK.feeds
        else:
            self.relationship_type = relationship_type

        self.update_position()

    def update_position(self):
        """Update the connection path based on port positions and joints."""
        if not self.source_port:
            return

        # Get source position
        source_pos = self.source_port.scenePos()

        # Clear existing arrows
        self._clear_arrows()

        # Draw complete path if target exists, or temporary path if in creation mode
        if self.target_port:
            self._draw_complete_path(source_pos, self.target_port.scenePos())

        elif hasattr(self, 'current_end_pos'):
            self._draw_temp_path(source_pos, self.current_end_pos)

    def _clear_arrows(self):
        """Remove all arrow indicators from the scene."""
        for arrow in self.arrows:
            if arrow.scene():
                arrow.scene().removeItem(arrow)
        self.arrows.clear()

    def _draw_complete_path(self, source_pos, target_pos):
        """Draw a complete path with arrows from source to target through joints."""
        # Collect all points in order
        points = [source_pos] + [joint.scenePos() for joint in self.joints] + [target_pos]

        # Create path through all points
        path = QPainterPath()
        path.moveTo(source_pos)

        # Draw segments and add arrows
        for i in range(1, len(points)):
            start_point = points[i - 1]
            end_point = points[i]

            path.lineTo(end_point)
            self._add_arrow_to_segment(start_point, end_point)

        self.setPath(path)

    def _draw_temp_path(self, source_pos, end_pos):
        """Draw a temporary path during connection creation."""
        # Collect all points in order
        points = [source_pos] + [joint.scenePos() for joint in self.joints] + [end_pos]

        # Create path through all points
        path = QPainterPath()
        path.moveTo(source_pos)

        # Draw segments and add arrows to all except last segment
        for i in range(1, len(points)):
            start_point = points[i - 1]
            end_point = points[i]

            path.lineTo(end_point)

            # Only add arrows to completed segments (not to temporary end segment)
            if i < len(points) - 1 or self.target_port:
                self._add_arrow_to_segment(start_point, end_point)

        self.setPath(path)

    def _add_arrow_to_segment(self, start_point, end_point):
        """Add a directional arrow in the middle of a line segment."""
        # Calculate arrow position and orientation

        middle_x = (start_point.x() + end_point.x()) / 2
        middle_y = (start_point.y() + end_point.y()) / 2

        angle = math.atan2(end_point.y() - start_point.y(),
                           end_point.x() - start_point.x())

        # Define arrow shape
        arrow_size = 5
        arrow_angle = math.pi / 4  # 45 degrees (wider angle = less pointy)

        # Point2 should be the tip of the arrow pointing toward the end point
        point2 = QPointF(
            middle_x + arrow_size * math.cos(angle),
            middle_y + arrow_size * math.sin(angle)
        )

        # Calculate arrowhead base points with wider angle
        point1 = QPointF(
            middle_x + arrow_size * math.cos(angle + math.pi - arrow_angle),
            middle_y + arrow_size * math.sin(angle + math.pi - arrow_angle)
        )

        point3 = QPointF(
            middle_x + arrow_size * math.cos(angle + math.pi + arrow_angle),
            middle_y + arrow_size * math.sin(angle + math.pi + arrow_angle)
        )

        # Create arrow polygon
        polygon = QPolygonF([point1, point2, point3])
        arrow = QGraphicsPolygonItem(polygon)

        # Match arrow style to connection
        arrow.setBrush(QBrush(self.pen().color()))
        arrow.setPen(self.pen())

        # Add to scene
        if self.scene():
            self.scene().addItem(arrow)

        # Store reference
        self.arrows.append(arrow)

        return arrow

    def set_current_end_pos(self, pos):
        """Set temporary end position during connection creation."""
        self.current_end_pos = pos
        self.update_position()

    def set_target_port(self, target_port):
        """Set the target port and finalize the connection."""
        # Remove from previous target if exists
        if self.target_port:
            self.target_port.remove_connection(self)

        self.target_port = target_port

        if target_port:
            target_port.add_connection(self)

        self.update_position()

    def remove(self):
        """Remove this connection from the scene and all related elements."""
        # Unregister from ports
        if self.source_port:
            self.source_port.remove_connection(self)

        if self.target_port:
            self.target_port.remove_connection(self)

        # Remove joints
        for joint in self.joints:
            if joint.scene():
                joint.scene().removeItem(joint)
        self.joints.clear()

        # Remove arrows
        self._clear_arrows()

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)

    def reverse(self):
        """Reverse connection direction by swapping source and target ports."""
        source = self.source_port
        target = self.target_port

        self.source_port = target
        self.target_port = source

        self.update_position()

    def set_relationship_type(self, rel_type):
        """Set the semantic relationship type for this connection with visual styling."""

        self.relationship_type = rel_type

        # Determine line style based on relationship type
        if rel_type == rdflib.BRICK.hasPoint or rel_type == rdflib.BRICK.isPointOf:
            line_style = Qt.DashLine
        else:
            line_style = Qt.SolidLine

        # Create new pen with appropriate style
        current_pen = self.pen()
        new_pen = QPen(current_pen)
        new_pen.setStyle(line_style)

        # Apply new pen to connection
        self.setPen(new_pen)

        # Update arrow styles to match
        current_color = current_pen.color()
        for arrow in self.arrows:
            arrow.setPen(new_pen)
            arrow.setBrush(QBrush(current_color))

    def get_source_entity_uri(self):
        """Get the source entity instance URI."""
        if self.source_port and self.source_port.entity_item:
            return self.source_port.entity_item.instance_uri
        return None

    def get_target_entity_uri(self):
        """Get the target entity instance URI."""
        if self.target_port and self.target_port.entity_item:
            return self.target_port.entity_item.instance_uri
        return None

    def add_joint_at_point(self, scene_pos: QPointF):
        """Add a routing joint at the specified position."""

        joint = JointItem(self)

        grid_size = AppConfig.grid_size

        # Snap position to grid
        x = round(scene_pos.x() / grid_size) * grid_size
        y = round(scene_pos.y() / grid_size) * grid_size

        joint.setPos(QPointF(x, y))

        # Add to scene
        if self.scene():
            self.scene().addItem(joint)

        # Add to joints list
        self.joints.append(joint)

        # Update path
        self.update_position()

        return joint
