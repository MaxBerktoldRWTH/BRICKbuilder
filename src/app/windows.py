from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QToolBar,
    QDockWidget, QMenu, QMessageBox, QToolButton,
    QFileDialog,
)
from PyQt5.QtGui import (
    QDragEnterEvent, QDragMoveEvent, QDropEvent,
)
from PyQt5.QtCore import Qt

from src.app.widgets import (
    EntityBrowser, PropertyPanel, Canvas,
)

from src.ifc import extract_topology


class DiagramApplication(QMainWindow):
    """Main application window for the building system design tool."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Building Systems Design with Brick and REC Ontologies")
        self.resize(1200, 800)

        self._setup_ui()
        # For your QMainWindow

        self.setAcceptDrops(True)

        # OR for your QGraphicsView
        self.canvas.setAcceptDrops(True)

    def _setup_ui(self):

        # Create entity browser dock
        self._setup_entity_browser()

        # Create property panel dock
        self._setup_property_panel()

        # Create canvas as central widget
        self._setup_canvas()

        # Add menu bar
        self._setup_menu_bar()

        # Add toolbar
        self._setup_toolbar()

        self.statusBar().showMessage("Ready")

    def _setup_entity_browser(self):
        """Create and configure entity browser dock widget."""

        entity_tree = EntityBrowser()
        entity_dock = QDockWidget("Entities", self)
        entity_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        entity_dock.setWidget(entity_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, entity_dock)

    def _setup_property_panel(self):
        """Create and configure property panel dock widget."""

        self.property_panel = PropertyPanel()
        properties_dock = QDockWidget("Properties", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        properties_dock.setWidget(self.property_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, properties_dock)

    def _setup_canvas(self):

        # Create canvas as central widget
        self.canvas = Canvas(properties_panel=self.property_panel)
        self.setCentralWidget(self.canvas)

    def _setup_toolbar(self):
        """Create and configure application toolbar."""

        toolbar = QToolBar("Entity Tools", self)
        self.addToolBar(toolbar)

        # Add rotation action
        rotate_action = QAction("Rotate 90°", self)
        rotate_action.setStatusTip("Rotate selected entities by 90 degrees")
        rotate_action.setShortcut("r")
        rotate_action.triggered.connect(self.canvas._rotate_selected_entities)
        toolbar.addAction(rotate_action)

        # Add zoom dropdown
        zoom_button = QToolButton()
        zoom_button.setText("Zoom")
        zoom_button.setPopupMode(QToolButton.InstantPopup)

        zoom_menu = QMenu()

        # Zoom in action
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(lambda: self._zoom_in())
        zoom_menu.addAction(zoom_in_action)

        # Zoom out action
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(lambda: self._zoom_out())
        zoom_menu.addAction(zoom_out_action)

        # Reset zoom action
        zoom_reset_action = QAction("Reset Zoom", self)
        zoom_reset_action.triggered.connect(self._reset_zoom)
        zoom_menu.addAction(zoom_reset_action)

        zoom_button.setMenu(zoom_menu)
        toolbar.addWidget(zoom_button)

    def _zoom_in(self):
        """Zoom in with notification."""
        self.canvas.scale(1.2, 1.2)

        self.statusBar().showMessage("Zoomed in")

    def _zoom_out(self):
        """Zoom out with notification."""

        self.canvas.scale(1 / 1.2, 1 / 1.2)
        self.statusBar().showMessage("Zoomed out")

    def _reset_zoom(self):
        """Reset canvas zoom to 100%."""

        self.canvas.resetTransform()
        self.statusBar().showMessage("Zoom reset to 100%")

    def _setup_menu_bar(self):
        """Create and configure application menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        export_action = QAction("Export to Turtle (.ttl)", self)
        export_action.setShortcut("Ctrl+s")
        export_action.setStatusTip("Export the design as an ontology Turtle file")
        export_action.triggered.connect(self._export_to_turtle)
        file_menu.addAction(export_action)

        import_action = QAction("Import from Turtle (.ttl)", self)
        import_action.setShortcut("Ctrl+i")
        import_action.setStatusTip("Import an ontology Turtle file")
        import_action.triggered.connect(self._import_from_turtle)
        file_menu.addAction(import_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")

        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Del")
        delete_action.setStatusTip("Delete selected items")
        delete_action.triggered.connect(self.canvas._delete_selected_items)
        edit_menu.addAction(delete_action)

        # copy_action = QAction("Copy", self)
        # copy_action.setShortcut("Ctrl+C")
        # copy_action.setStatusTip("Copy selected items")
        # copy_action.triggered.connect(self.canvas._copy_selected_items)
        # edit_menu.addAction(copy_action)

        # paste_action = QAction("Paste", self)
        # paste_action.setShortcut("Ctrl+V")
        # paste_action.setStatusTip("Paste copied items")
        # paste_action.triggered.connect(self.canvas._paste_copied_items)
        # edit_menu.addAction(paste_action)

        # View menu (single definition)
        view_menu = menu_bar.addMenu("View")

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        # Add a separator
        view_menu.addSeparator()

        # In your _setup_menu_bar method
        view_menu.addSeparator()
        toggle_points_action = QAction("Toggle Points Visibility", self)
        toggle_points_action.setShortcut("P")
        toggle_points_action.setCheckable(True)
        toggle_points_action.setChecked(True)
        toggle_points_action.triggered.connect(self.canvas.toggle_points_visibility)
        view_menu.addAction(toggle_points_action)

    def _export_to_turtle(self):
        """Export the current design to a Turtle file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Turtle File", "", "Turtle Files (*.ttl)")

        if file_path:
            if not file_path.endswith('.ttl'):
                file_path += '.ttl'

            try:
                success = self.canvas.save_to_turtle(file_path)
                if success:
                    self.statusBar().showMessage(f"Design saved to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error saving design: {str(e)}")
                print(f"Export error: {e}")

    def _import_from_turtle(self):
        """Import a design from a Turtle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Turtle File", "", "Turtle Files (*.ttl)")

        if file_path:
            try:
                success = self.canvas.load_from_turtle(file_path)
                if success:
                    self.statusBar().showMessage(f"Design loaded from {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Error loading design: {str(e)}")
                print(f"Import error: {e}")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.ifc'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.ifc'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:

        if event.mimeData().hasUrls():
            ifc_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.ifc'):
                    ifc_files.append(file_path)

            if len(ifc_files) != 1:
                raise ValueError(f"Please load only one IFC file at a time. Got {len(ifc_files)} files.")

            graph = extract_topology(ifc_files[0])

            print(f'Extracted graph with {len(graph)} triples from {ifc_files[0]}')

            self.canvas.import_from_graph(graph)

            event.acceptProposedAction()
