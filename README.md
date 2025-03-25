# Building Systems Design Tool

This application provides a graphical interface for designing building systems using the Brick and REC ontologies. It allows you to create, visualize, and export semantic models of building systems with entities, connections, and their relationships.

## Core Functionality

### Entity Modeling
- **Entity Library**: Browse and use a comprehensive collection of Brick and REC entity types organized by category (Equipment, Sensors, Points, Spaces, etc.)
- **Drag-and-Drop Interface**: Easily add entities to your design by dragging them from the entity browser to the canvas
- **Properties Panel**: View and edit entity properties, labels, and positions

### Semantic Relationships
- **Visual Connections**: Create semantically meaningful connections between entities with proper Brick relationship types
- **Smart Routing**: Use joints to create custom routing paths for connections
- **Relationship Types**: Automatically assigns appropriate relationship types (e.g., hasPoint/isPointOf for sensor connections)

### Design Management
- **Export to Turtle**: Save your designs as standard RDF Turtle (.ttl) files for use with other semantic tools
- **Import from Turtle**: Load previously saved designs back into the application (Example file: `data/TTL/boptest_multizone.ttl`)
- **IFC Import**: Import building layouts directly from IFC files via drag-and-drop

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| H | Show help window with all shortcuts |
| Del | Delete selected items |
| Ctrl+A | Select all items |
| R | Rotate selected entities 90° |
| Ctrl+C | Copy selected items |
| Ctrl+V | Paste copied items |
| P | Toggle visibility of Points and their connections |
| Ctrl+scroll | Zoom in/out |
| Middle mouse button | Pan the canvas |
| +/- | Zoom in/out |
| Ctrl+S | Export design to Turtle file |
| Ctrl+I | Import design from Turtle file |

## Working with Connections

1. **Creating Connections**: Click and drag from one entity's port to another
2. **Adding Routing Points**: Double-click on a connection to add a routing joint
3. **Moving Joints**: Click and drag joints to reposition connection paths
4. **Changing Relationship Types**: Select a connection and change its relationship type in the properties panel
5. **Reversing Direction**: Use the "Reverse Direction" button in the properties panel

## IFC Import Feature

The application can import building layouts directly from IFC (Industry Foundation Classes) files:

1. Simply drag and drop an IFC file onto the application window
2. The tool will automatically extract:
   - Buildings
   - Levels (storeys)
   - Rooms and spaces
3. Imported elements are arranged in a structured layout with proper semantic relationships
4. Once imported, you can add equipment, points, and other entities to the spaces

This feature provides a quick way to create the spatial context for your building systems designs based on architectural models.
To test this feature there is an example `boptest_multizone.ifc` file in the `data/IFC/` folder. 

## UI Components

- **Entity Browser**: Left panel showing available entity types organized by category
- **Canvas**: Central area for creating and editing the building system design
- **Property Panel**: Right panel for viewing and editing properties of selected items
- **Toolbar**: Quick access to common tools like rotate and zoom
- **Menus**: Access to file operations, editing functions, and view options

## Getting Started

1. Browse entities in the left panel
2. Drag entities onto the canvas to create your design
3. Connect entities by clicking and dragging between their ports
4. Use the properties panel to set entity labels and connection types
5. Save your work using File > Export to Turtle

For spatial context, either create rooms manually or drag-and-drop an IFC file to import the building layout.


# The complete code, including this readme was written by claude 3.7!
