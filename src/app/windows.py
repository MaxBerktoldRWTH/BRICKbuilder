import rdflib

from PyQt5.QtWidgets import (
    QMainWindow, QAction, QToolBar, QFileDialog,
    QDockWidget, QMenu, QMessageBox, QToolButton,
)
from PyQt5.QtGui import (
    QDragEnterEvent, QDragMoveEvent, QDropEvent,
)
from PyQt5.QtCore import Qt

from src.app.widgets import (
    EntityBrowser, PropertyPanel, Canvas,
)

from src.ifc import extract_topology
from src.app.items import EntityItem, ConnectionItem
from src.validation.shacl import validate_graph_with_shacl
from src.app.shacl_dialogs import ShaclValidationReportDialog
from src.ontologies.reasoning import reason_with_owlrl


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

        self.shacl_file_path = None  # Store the SHACL file path for validation

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

        # Validation menu
        validation_menu = menu_bar.addMenu("Validation")

        load_shacl_action = QAction("Load SHACL Shapes (.ttl)", self)
        load_shacl_action.setStatusTip("Load a SHACL shapes file")
        load_shacl_action.triggered.connect(self._load_shacl_file)
        validation_menu.addAction(load_shacl_action)

        validate_shacl_action = QAction("Validate with SHACL", self)
        validate_shacl_action.setShortcut("Ctrl+Shift+V")
        validate_shacl_action.setStatusTip("Validate the current design using the loaded SHACL shapes")
        validate_shacl_action.triggered.connect(self._validate_with_shacl)
        validation_menu.addAction(validate_shacl_action)

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

        print("dragEnterEvent triggered")
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"Drag enter with file: {file_path}")
                if file_path.lower().endswith(('.ttl', '.ifc')):
                    print(f"Accepting file: {file_path}")
                    event.acceptProposedAction()
                    return

        print("Ignoring drag enter event")
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.ttl', '.ifc')):
                    event.acceptProposedAction()
                    return

        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        print("dropEvent triggered")
        if event.mimeData().hasUrls():
            ttl_files = []
            ifc_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"Drop file: {file_path}")
                if file_path.lower().endswith('.ttl'):
                    ttl_files.append(file_path)
                elif file_path.lower().endswith('.ifc'):
                    ifc_files.append(file_path)

            if ttl_files:
                print(f"Processing {len(ttl_files)} TTL files")

                # Process ttl files (import without clearing)
                for ttl_file in ttl_files:
                    try:
                        print(f"Importing TTL file: {ttl_file}")
                        # Load the TTL file directly without URI replacement
                        # This simpler approach may help identify if the issue is in the complex URI handling
                        self.canvas.load_from_turtle(ttl_file)
                        self.statusBar().showMessage(f"Imported {ttl_file}")
                        print(f"Successfully imported {ttl_file}")
                    except Exception as e:
                        error_msg = f"Error importing {ttl_file}: {str(e)}"
                        print(error_msg)
                        QMessageBox.critical(self, "Import Error", error_msg)

                event.acceptProposedAction()
                return

            if ifc_files:
                print(f"Processing {len(ifc_files)} IFC files")

                for ifc_file in ifc_files:
                    try:
                        print(f"Importing TTL file: {ifc_file}")

                        self.canvas.load_from_ifc(ifc_file)
                        self.statusBar().showMessage(f"Imported {ifc_file}")
                        print(f"Successfully imported {ifc_file}")
                    except Exception as e:
                        error_msg = f"Error importing {ifc_file}: {str(e)}"
                        print(error_msg)
                        QMessageBox.critical(self, "Import Error", error_msg)

        print("Ignoring drop event")
        event.ignore()

    def _collect_existing_uris(self):
        """Collect all existing instance URIs from canvas items."""

        existing_uris = set()

        for item in self.canvas.scene.items():
            if isinstance(item, EntityItem):
                existing_uris.add(str(item.instance_uri))
            elif isinstance(item, ConnectionItem):
                existing_uris.add(str(item.instance_uri))

        return existing_uris

    def _replace_instance_uris(self, graph, existing_uris):
        """Replace instance URIs in the graph to avoid conflicts with existing ones."""
        import uuid
        from src.config import AppConfig

        # Create a new graph to hold the updated triples
        new_graph = rdflib.Graph()

        # Create a mapping of old URIs to new URIs
        uri_mapping = {}

        # First pass: Collect all URIs that need to be replaced
        for subj, pred, obj in graph:
            if isinstance(subj, rdflib.URIRef) and str(subj).startswith(str(AppConfig.building_ns)):
                if str(subj) in existing_uris and str(subj) not in uri_mapping:
                    uri_mapping[str(subj)] = str(AppConfig.building_ns[str(uuid.uuid4())])

            if isinstance(obj, rdflib.URIRef) and str(obj).startswith(str(AppConfig.building_ns)):
                if str(obj) in existing_uris and str(obj) not in uri_mapping:
                    uri_mapping[str(obj)] = str(AppConfig.building_ns[str(uuid.uuid4())])

        # Second pass: Add triples with replaced URIs
        for subj, pred, obj in graph:
            new_subj = rdflib.URIRef(uri_mapping.get(str(subj), str(subj)))
            new_obj = obj

            if isinstance(obj, rdflib.URIRef):
                new_obj = rdflib.URIRef(uri_mapping.get(str(obj), str(obj)))

            new_graph.add((new_subj, pred, new_obj))

        # Copy over namespace bindings
        for prefix, namespace in graph.namespaces():
            new_graph.bind(prefix, namespace)

        return new_graph

    def _load_shacl_file(self):
        """
        Let the user select a SHACL Turtle file.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load SHACL Shapes File",
            "",
            "Turtle Files (*.ttl);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Parse once to fail early if file is invalid.
            test_graph = rdflib.Graph()
            test_graph.parse(file_path, format="turtle")

            self.shacl_file_path = file_path
            self.statusBar().showMessage(f"Loaded SHACL shapes: {file_path}")

            QMessageBox.information(
                self,
                "SHACL Shapes Loaded",
                f"Loaded SHACL shapes file:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "SHACL Load Error",
                f"Could not load SHACL shapes file:\n{str(e)}"
            )

    def _validate_with_shacl(self):
        """
        Validate the current canvas RDF graph against the loaded SHACL shapes.
        """
        if not self.shacl_file_path:
            QMessageBox.warning(
                self,
                "No SHACL File",
                "Please load a SHACL shapes file first."
            )
            return

        try:
            data_graph = self.canvas.to_rdf_graph()

            from src.ontologies.graphs import BRICK_GRAPH

            data_graph = reason_with_owlrl(data_graph + BRICK_GRAPH())

            validation_result = validate_graph_with_shacl(
                data_graph=data_graph,
                shacl_file_path=self.shacl_file_path,
                inference="rdfs",
                abort_on_first=False,
                allow_warnings=False,
                allow_infos=False,
            )

            if validation_result.conforms:
                self.statusBar().showMessage("SHACL validation passed")
                QMessageBox.information(
                    self,
                    "SHACL Validation Passed",
                    "The current design conforms to the loaded SHACL constraints."
                )
            else:
                self.statusBar().showMessage(
                    f"SHACL validation failed: {len(validation_result.violations)} result(s)"
                )

                dialog = ShaclValidationReportDialog(
                    validation_result=validation_result,
                    parent=self
                )
                dialog.exec_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "SHACL Validation Error",
                f"An error occurred during SHACL validation:\n{str(e)}"
            )