import uuid
import rdflib

# PyQt imports
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QGraphicsView, QGraphicsScene, QMessageBox, QColorDialog,
    QComboBox, QFormLayout, QLineEdit, QPushButton, QGroupBox,
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, pyqtSignal, QByteArray, QMimeData, QPoint
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QIcon, QPixmap, QPainter, QDrag, QTransform
)
from PyQt5.QtSvg import QSvgRenderer

# Local imports
from src.model import EntityLibrary, Point
from src.app.items import EntityItem, ConnectionItem, PortItem, JointItem
from src.config import AppConfig
from src.logging import Logger
from src.app.dialogs import ExternalReferencesDialog
from src.ifc import extract_topology
from src.ontologies.namespaces import RDF, BLDG, REC, BRICK, BRICK_REF, VISU, BACNET, bind_namespaces, short_uuid

# Ontology namespace definitions
BRICK_RELATIONSHIPS = {
    "hasLocation": rdflib.BRICK.hasLocation,
    "isLocationOf": rdflib.BRICK.isLocationOf,
    "feeds": rdflib.BRICK.feeds,
    "isFedBy": rdflib.BRICK.isFedBy,
    "hasPoint": rdflib.BRICK.hasPoint,
    "isPointOf": rdflib.BRICK.isPointOf,
    "hasPart": rdflib.BRICK.hasPart,
    "isPartOf": rdflib.BRICK.isPartOf,
}


class PropertyPanel(QWidget):
    """Panel for viewing and editing properties of selected entities and connections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_selection = []
        self._setup_ui()

    @property
    def current_item(self):
        """Get the first selected item from the current selection."""
        if self.current_selection and len(self.current_selection) > 0:
            return self.current_selection[0]
        return None

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Selection count label
        self.selection_count_label = QLabel("")
        layout.addWidget(self.selection_count_label)

        # --- Entity Form Group ---
        self.entity_widget = QWidget()
        self.entity_form = QFormLayout(self.entity_widget)
        self.entity_form.setContentsMargins(0, 0, 0, 0)

        # Type URI field
        self.type_uri_label = QLabel("")
        self.type_uri_label.setWordWrap(True)
        self.entity_form.addRow(QLabel("<b>Type URI:</b>"), self.type_uri_label)

        # Instance URI field
        self.instance_uri_label = QLabel("")
        self.instance_uri_label.setWordWrap(True)
        self.entity_form.addRow(QLabel("<b>Instance URI:</b>"), self.instance_uri_label)

        # Label field
        self.label_edit = QLineEdit("")
        self.label_edit.textChanged.connect(self._update_entity_label)
        self.entity_form.addRow(QLabel("<b>Label:</b>"), self.label_edit)

        # Position field
        self.position_label = QLabel("")
        self.entity_form.addRow(QLabel("<b>Position:</b>"), self.position_label)

        # Rotation field
        self.rotation_label = QLabel("")
        self.entity_form.addRow(QLabel("<b>Rotation:</b>"), self.rotation_label)

        # --- ADD External Reference Section (Initially Hidden) ---
        self.external_ref_group = QGroupBox("External Reference")  # Use GroupBox for clarity
        self.external_ref_layout = QVBoxLayout(self.external_ref_group)
        self.external_ref_group.setVisible(False)  # Hide the whole group initially

        # Reference Type Dropdown
        self.ref_type_combo = QComboBox()
        self.ref_type_combo.addItem("None", None)
        self.ref_type_combo.addItem("Timeseries", "Timeseries")
        self.ref_type_combo.addItem("BACnet", "BACnet")
        self.ref_type_combo.currentIndexChanged.connect(self._on_ref_type_changed)
        self.external_ref_layout.addWidget(QLabel("Reference Type:"))
        self.external_ref_layout.addWidget(self.ref_type_combo)

        # --- Timeseries Fields Container ---
        self.timeseries_ref_widget = QWidget()
        self.timeseries_ref_form = QFormLayout(self.timeseries_ref_widget)
        self.timeseries_ref_form.setContentsMargins(5, 5, 5, 5)  # Add some margin

        self.timeseries_id_edit = QLineEdit()
        self.timeseries_id_edit.setPlaceholderText("e.g., building1/sensor5/ts")
        self.timeseries_id_edit.textChanged.connect(self._update_external_ref_data)
        self.timeseries_ref_form.addRow("Timeseries ID:", self.timeseries_id_edit)

        self.timeseries_storedat_edit = QLineEdit()
        self.timeseries_storedat_edit.setPlaceholderText("e.g., influxdb://host:port/db")
        self.timeseries_storedat_edit.textChanged.connect(self._update_external_ref_data)
        self.timeseries_ref_form.addRow("Stored At (URI):", self.timeseries_storedat_edit)

        self.external_ref_layout.addWidget(self.timeseries_ref_widget)
        self.timeseries_ref_widget.setVisible(False)  # Initially hidden

        # --- BACnet Fields Container ---
        self.bacnet_ref_widget = QWidget()
        bacnet_layout = QVBoxLayout(self.bacnet_ref_widget)  # Use QVBoxLayout to stack option combo and form
        bacnet_layout.setContentsMargins(0, 0, 0, 0)

        # --- BACnet Option 1 Fields ---
        self.bacnet_option1_widget = QWidget()
        self.bacnet_ref_form = QFormLayout(self.bacnet_option1_widget)
        self.bacnet_ref_form.setContentsMargins(5, 5, 5, 5)

        self.bacnet_obj_id_edit = QLineEdit()
        self.bacnet_obj_id_edit.setPlaceholderText("e.g., analog-input,1")
        self.bacnet_obj_id_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_ref_form.addRow("Object Identifier:", self.bacnet_obj_id_edit)

        self.bacnet_obj_name_edit = QLineEdit()
        self.bacnet_obj_name_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_ref_form.addRow("Object Name:", self.bacnet_obj_name_edit)

        self.bacnet_obj_type_edit = QLineEdit()
        self.bacnet_obj_type_edit.setPlaceholderText("e.g., analogInput")
        self.bacnet_obj_type_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_ref_form.addRow("Object Type:", self.bacnet_obj_type_edit)

        self.bacnet_prop_id_edit = QLineEdit()
        self.bacnet_prop_id_edit.setPlaceholderText("e.g., presentValue")
        self.bacnet_prop_id_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_ref_form.addRow("Property Identifier:", self.bacnet_prop_id_edit)

        self.bacnet_dev_obj_id_edit = QLineEdit()
        self.bacnet_dev_obj_id_edit.setPlaceholderText("e.g., device,123 (Optional)")
        self.bacnet_dev_obj_id_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_ref_form.addRow("Device Object ID:", self.bacnet_dev_obj_id_edit)

        bacnet_layout.addWidget(self.bacnet_option1_widget)
        self.bacnet_option1_widget.setVisible(True)  # Option 1 is default

        # --- BACnet Option 2 Fields ---

        self.bacnet_uri_edit = QLineEdit()
        self.bacnet_uri_edit.setPlaceholderText("bacnet://<device>/<objtype>,<instance>/<prop>")
        self.bacnet_uri_edit.textChanged.connect(self._update_external_ref_data)
        self.bacnet_uri_dev_obj_id_edit = QLineEdit()
        self.bacnet_uri_dev_obj_id_edit.setPlaceholderText("e.g., device,123 (Optional)")
        self.bacnet_uri_dev_obj_id_edit.textChanged.connect(self._update_external_ref_data)

        self.external_ref_layout.addWidget(self.bacnet_ref_widget)
        self.bacnet_ref_widget.setVisible(False)  # Initially hidden

        # --- Add the GroupBox to the main entity form ---
        self.entity_form.addRow(self.external_ref_group)

        # --- End External Reference Section ---

        layout.addWidget(self.entity_widget)  # Add the entity group widget

        # --- Relationship Form Group ---
        self.relationship_widget = QWidget()  # Container for relationship fields
        self.relationship_form = QFormLayout(self.relationship_widget)
        self.relationship_form.setContentsMargins(0, 0, 0, 0)  # Optional: remove padding

        # Relationship URI
        self.rel_instance_uri_label = QLabel("")
        self.rel_instance_uri_label.setWordWrap(True)
        self.relationship_form.addRow(QLabel("<b>Instance URI:</b>"), self.rel_instance_uri_label)

        # Relationship type
        self.rel_type_uri_label = QLabel("")
        self.rel_type_uri_label.setWordWrap(True)
        self.relationship_form.addRow(QLabel("<b>Type URI:</b>"), self.rel_type_uri_label)

        # Source entity
        self.source_entity_label = QLabel("")
        self.source_entity_label.setWordWrap(True)
        self.relationship_form.addRow(QLabel("<b>Source:</b>"), self.source_entity_label)

        # Target entity
        self.target_entity_label = QLabel("")
        self.target_entity_label.setWordWrap(True)
        self.relationship_form.addRow(QLabel("<b>Target:</b>"), self.target_entity_label)

        # Relationship type dropdown
        self.rel_type_combo = QComboBox()
        for rel_name, rel_uri in BRICK_RELATIONSHIPS.items():
            self.rel_type_combo.addItem(rel_name, rel_uri)
        self.rel_type_combo.currentIndexChanged.connect(self._update_relationship_type)
        self.relationship_form.addRow(QLabel("<b>Type:</b>"), self.rel_type_combo)

        # Direction button
        self.reverse_button = QPushButton("Reverse Direction")
        self.reverse_button.clicked.connect(self._reverse_connection_direction)
        self.relationship_form.addRow(QLabel("<b>Direction:</b>"), self.reverse_button)

        # Color picker button
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self._choose_connection_color)
        self.relationship_form.addRow(QLabel("<b>Color:</b>"), self.color_button)

        layout.addWidget(self.relationship_widget)  # Add the relationship group widget

        # Hide forms initially
        self.relationship_widget.setVisible(False)
        self.entity_widget.setVisible(False)

        layout.addStretch(1)
        self.setMinimumWidth(300)  # Increase minimum width slightly

    def _update_entity_label(self):
        """Update the label of the selected entity."""
        # Only allow editing if a single item is selected
        if len(self.current_selection) == 1 and isinstance(self.current_item, EntityItem):
            new_label = self.label_edit.text()
            self.current_item.label = new_label

    # --- REVISED Show/Hide Logic ---
    def _hide_entity_form(self):
        self.entity_widget.setVisible(False)
        self.external_ref_group.setVisible(False)  # Also hide the ref group

    def _show_entity_form(self):
        self.entity_widget.setVisible(True)
        # Button visibility is handled separately in update_properties

    def _hide_relationship_form(self):
        self.relationship_widget.setVisible(False)

    def _show_relationship_form(self):
        self.relationship_widget.setVisible(True)

    # --- END REVISED Show/Hide Logic ---

    def update_properties(self, items=None):
        """Update the properties panel with the selected items' information."""
        self.current_selection = items if items else []

        # Block signals during update to prevent premature data writes
        self._block_all_ref_signals(True)

        # Hide all forms initially
        self._hide_entity_form()
        self._hide_relationship_form()
        # external_ref_group is hidden by _hide_entity_form

        if not self.current_selection:
            self.selection_count_label.setText("No items selected")
            self._show_entity_form()
            self.type_uri_label.setText("N/A")
            self.instance_uri_label.setText("N/A")
            self.label_edit.clear()
            self.label_edit.setPlaceholderText("")
            self.label_edit.setEnabled(False)
            self.position_label.setText("N/A")
            self.rotation_label.setText("N/A")
            self.external_ref_group.setVisible(False)  # Ensure hidden
            self._block_all_ref_signals(False)  # Unblock signals
            return

        entity_count = sum(1 for item in self.current_selection if isinstance(item, EntityItem))
        connection_count = sum(1 for item in self.current_selection if isinstance(item, ConnectionItem))

        if len(self.current_selection) == 1:
            self.selection_count_label.setText("1 item selected")
        else:
            self.selection_count_label.setText(f"{len(self.current_selection)} items selected")

        # Default state for ref section
        self.external_ref_group.setVisible(False)

        if len(self.current_selection) > 1:
            self._handle_multiple_selection(entity_count, connection_count)
        else:
            # Handle single item selection
            item = self.current_item
            if isinstance(item, EntityItem):
                self._update_entity_properties(item)  # Handles showing entity form
                # Show/hide reference section based on type
                if isinstance(item.entity, Point):
                    self.external_ref_group.setVisible(True)
                    self._load_external_ref_data(item)  # Load existing data
                else:
                    self.external_ref_group.setVisible(False)
            elif isinstance(item, ConnectionItem):
                self._update_connection_properties(item)  # Handles showing relationship form

        self._block_all_ref_signals(False)  # Unblock signals after updates

    def _load_external_ref_data(self, item: EntityItem):
        """Loads existing external reference data into the UI fields (Simplified)."""
        ref_data = item.get_external_reference()
        self._clear_ref_fields()

        if not ref_data:
            self.ref_type_combo.setCurrentIndex(0)  # "None"
            self._update_ref_fields_visibility()
            return

        ref_type = ref_data.get('type')

        if ref_type == "Timeseries":
            self.ref_type_combo.setCurrentIndex(self.ref_type_combo.findData("Timeseries"))
            self.timeseries_id_edit.setText(ref_data.get('timeseriesId', ''))
            self.timeseries_storedat_edit.setText(ref_data.get('storedAt', ''))
        elif ref_type == "BACnet":
            self.ref_type_combo.setCurrentIndex(self.ref_type_combo.findData("BACnet"))
            # Directly load into the property fields
            self.bacnet_obj_id_edit.setText(ref_data.get('object-identifier', ''))
            self.bacnet_obj_name_edit.setText(ref_data.get('object-name', ''))
            self.bacnet_obj_type_edit.setText(ref_data.get('object-type', ''))
            # Use 'property-identifier' as the primary key, fallback to 'read-property' for loading old data
            prop_id = ref_data.get('property-identifier', ref_data.get('read-property', ''))
            self.bacnet_prop_id_edit.setText(prop_id)
            self.bacnet_dev_obj_id_edit.setText(ref_data.get('objectOf', ''))
        else:
            self.ref_type_combo.setCurrentIndex(0)  # "None"

        self._update_ref_fields_visibility()

    def _clear_ref_fields(self):
        """Clears all external reference input fields (Simplified)."""
        self.timeseries_id_edit.clear()
        self.timeseries_storedat_edit.clear()
        self.bacnet_obj_id_edit.clear()
        self.bacnet_obj_name_edit.clear()
        self.bacnet_obj_type_edit.clear()
        self.bacnet_prop_id_edit.clear()
        self.bacnet_dev_obj_id_edit.clear()

    def _on_ref_type_changed(self):
        """Handles changes in the reference type dropdown."""
        self._update_ref_fields_visibility()
        self._update_external_ref_data()  # Update the stored data immediately

    def _update_ref_fields_visibility(self):
        """Shows/hides Timeseries or BACnet fields based on dropdown."""
        selected_type = self.ref_type_combo.currentData()

        self.timeseries_ref_widget.setVisible(selected_type == "Timeseries")
        self.bacnet_ref_widget.setVisible(selected_type == "BACnet")

    def _update_external_ref_data(self):
        """Updates the external_reference dictionary on the selected Point item."""
        if len(self.current_selection) != 1 or not isinstance(self.current_item, EntityItem) or not isinstance(
                self.current_item.entity, Point):
            return  # Only act on a single selected Point

        item = self.current_item
        selected_type = self.ref_type_combo.currentData()

        if selected_type is None:  # "None" selected
            item.clear_external_reference()
            return

        # Ensure the reference dictionary exists
        if item.external_reference is None or item.external_reference.get('type') != selected_type:
            # If switching type or creating new, start fresh dict
            item.external_reference = {'type': selected_type}
            # Add internal ID (optional but potentially useful)
            item.external_reference['id'] = str(uuid.uuid4())

        ref_data = item.external_reference  # Now we know it's a dict

        if selected_type == "Timeseries":
            ref_data['timeseriesId'] = self.timeseries_id_edit.text().strip()
            ref_data['storedAt'] = self.timeseries_storedat_edit.text().strip()
            # Remove potential BACnet keys if switching type
            ref_data.pop('option', None)
            ref_data.pop('object-identifier', None)
            # ... remove other BACnet keys ...
            ref_data.pop('BACnetURI', None)
            ref_data.pop('objectOf', None)

        elif selected_type == "BACnet":

            # Remove potential Timeseries keys
            ref_data.pop('timeseriesId', None)
            ref_data.pop('storedAt', None)

            ref_data['object-identifier'] = self.bacnet_obj_id_edit.text().strip()
            ref_data['object-name'] = self.bacnet_obj_name_edit.text().strip()
            ref_data['object-type'] = self.bacnet_obj_type_edit.text().strip()
            ref_data['property-identifier'] = self.bacnet_prop_id_edit.text().strip()  # Use 'property-identifier'
            ref_data['objectOf'] = self.bacnet_dev_obj_id_edit.text().strip()  # Use 'objectOf'
            # Clear option 2 field
            ref_data.pop('BACnetURI', None)

        # Clean up empty strings - store them as None or remove the key
        keys_to_remove = [k for k, v in ref_data.items() if isinstance(v, str) and not v]
        for k in keys_to_remove:
            del ref_data[k]

        # Update the item's reference
        item.set_external_reference(ref_data)
        print(f"Updated external ref: {item.external_reference}")  # Debug

    def _block_all_ref_signals(self, block: bool):
        """Blocks or unblocks signals for all reference input widgets."""
        self.ref_type_combo.blockSignals(block)
        self.timeseries_id_edit.blockSignals(block)
        self.timeseries_storedat_edit.blockSignals(block)
        self.bacnet_obj_id_edit.blockSignals(block)
        self.bacnet_obj_name_edit.blockSignals(block)
        self.bacnet_obj_type_edit.blockSignals(block)
        self.bacnet_prop_id_edit.blockSignals(block)
        self.bacnet_dev_obj_id_edit.blockSignals(block)
        self.bacnet_uri_edit.blockSignals(block)
        self.bacnet_uri_dev_obj_id_edit.blockSignals(block)

    def _handle_multiple_selection(self, entity_count, connection_count):
        """Handle display and editing for multiple selected items."""
        # Button is already hidden (set in update_properties)

        if entity_count > 0 and connection_count == 0:
            self._handle_multiple_entities(entity_count)
        elif entity_count == 0 and connection_count > 0:
            self._handle_multiple_connections(connection_count)
        else:
            self._handle_mixed_selection(entity_count, connection_count)

    def _handle_multiple_entities(self, count):
        """Handle when multiple entities are selected."""
        self._show_entity_form()  # Show the entity form container
        self.type_uri_label.setText(f"{count} entities selected")
        self.instance_uri_label.setText("Multiple instances")
        self.position_label.setText("Various positions")
        self.rotation_label.setText("Various rotations")

        entities = [item for item in self.current_selection if isinstance(item, EntityItem)]
        labels = set(entity.label for entity in entities)

        self.label_edit.setEnabled(True)  # Allow editing label even for multiple
        if len(labels) == 1:
            self.label_edit.blockSignals(True)
            self.label_edit.setText(next(iter(labels)))
            self.label_edit.setPlaceholderText("")
            self.label_edit.blockSignals(False)
        else:
            self.label_edit.blockSignals(True)
            self.label_edit.clear()
            self.label_edit.setPlaceholderText("Multiple values...")
            self.label_edit.blockSignals(False)
        # Button remains hidden

    def _handle_multiple_connections(self, count):
        """Handle when multiple connections are selected."""
        self._show_relationship_form()  # Show relationship form
        self.rel_instance_uri_label.setText(f"{count} connections selected")
        self.rel_type_uri_label.setText("Multiple connections")
        self.source_entity_label.setText("Various sources")
        self.target_entity_label.setText("Various targets")

        connections = [item for item in self.current_selection if isinstance(item, ConnectionItem)]
        rel_types = set(conn.relationship_type for conn in connections)

        if len(rel_types) == 1:
            rel_type = next(iter(rel_types))
            found = False
            for i in range(self.rel_type_combo.count()):
                if self.rel_type_combo.itemData(i) == rel_type:
                    self.rel_type_combo.blockSignals(True)
                    self.rel_type_combo.setCurrentIndex(i)
                    self.rel_type_combo.blockSignals(False)
                    found = True
                    break
            if not found:  # Handle case where saved type isn't in dropdown
                self.rel_type_combo.blockSignals(True)
                self.rel_type_combo.setCurrentIndex(-1)
                self.rel_type_combo.blockSignals(False)
        else:
            # Different types
            self.rel_type_combo.blockSignals(True)
            self.rel_type_combo.setCurrentIndex(-1)  # Indicate multiple types
            self.rel_type_combo.blockSignals(False)
        # Button remains hidden

    def _handle_mixed_selection(self, entity_count, connection_count):
        """Handle when both entities and connections are selected."""
        self._show_entity_form()  # Show entity form (mostly disabled)
        self.type_uri_label.setText(f"{entity_count} entities, {connection_count} connections")
        self.instance_uri_label.setText("Multiple instances")
        self.position_label.setText("Various positions")
        self.rotation_label.setText("Various rotations")

        self.label_edit.blockSignals(True)
        self.label_edit.clear()
        self.label_edit.setPlaceholderText("Cannot edit mixed selection")
        self.label_edit.setEnabled(False)
        self.label_edit.blockSignals(False)
        # Button remains hidden

    def _update_entity_properties(self, entity_item):
        """Update the panel with entity properties."""
        self._show_entity_form()  # Ensure container is visible
        self.type_uri_label.setText(str(entity_item.entity.uri_ref))
        self.instance_uri_label.setText(str(entity_item.instance_uri))

        self.label_edit.blockSignals(True)
        self.label_edit.setText(entity_item.label)
        self.label_edit.setEnabled(True)  # Enable label editing
        self.label_edit.setPlaceholderText("")
        self.label_edit.blockSignals(False)

        pos = entity_item.pos()
        # Use .1f for one decimal place, or adjust as needed
        self.position_label.setText(f"({pos.x():.1f}, {pos.y():.1f})")
        # Use correct degree symbol if possible, otherwise 'deg'
        self.rotation_label.setText(f"{entity_item.rotation_angle}°")

        # Button visibility is handled in update_properties after this call

    def _update_connection_properties(self, connection_item):
        """Update the panel with connection properties."""
        self._show_relationship_form()  # Ensure container is visible
        self.rel_instance_uri_label.setText(str(connection_item.instance_uri))
        self.rel_type_uri_label.setText(str(connection_item.relationship_type))

        source_uri = connection_item.get_source_entity_uri()
        self.source_entity_label.setText(str(source_uri) if source_uri else "Unknown source")

        target_uri = connection_item.get_target_entity_uri()
        self.target_entity_label.setText(str(target_uri) if target_uri else "Unknown target")

        # Set relationship type in combo box
        found = False
        for i in range(self.rel_type_combo.count()):
            if self.rel_type_combo.itemData(i) == connection_item.relationship_type:
                self.rel_type_combo.blockSignals(True)
                self.rel_type_combo.setCurrentIndex(i)
                self.rel_type_combo.blockSignals(False)
                found = True
                break
        if not found:  # Clear combo if type not found
            self.rel_type_combo.blockSignals(True)
            self.rel_type_combo.setCurrentIndex(-1)
            self.rel_type_combo.blockSignals(False)

        # Set color button background
        current_color = connection_item.pen().color()
        self.color_button.setStyleSheet(f"background-color: {current_color.name()}")

        # Button visibility is handled in update_properties

    def _update_relationship_type(self, index):
        """Update the relationship type for all selected connections."""
        if index < 0 or not self.current_selection:  # Check index and selection
            return

        rel_type = self.rel_type_combo.itemData(index)
        if not rel_type:  # Ensure data is valid
            return

        for item in self.current_selection:
            if isinstance(item, ConnectionItem):
                item.set_relationship_type(rel_type)
        # Update the display for the current item if it's a connection
        if isinstance(self.current_item, ConnectionItem):
            self.rel_type_uri_label.setText(str(rel_type))

    def _choose_connection_color(self):
        """Open color dialog to choose connection color for all selected connections."""
        connections = [item for item in self.current_selection if isinstance(item, ConnectionItem)]
        if not connections:
            return

        current_color = connections[0].pen().color()
        color = QColorDialog.getColor(current_color, self, "Choose Connection Color")

        if color.isValid():
            for item in connections:
                item_pen = item.pen()
                new_pen = QPen(item_pen)
                new_pen.setColor(color)
                item.setPen(new_pen)
                # Update arrows immediately
                for arrow in item.arrows:
                    arrow.setPen(new_pen)
                    arrow.setBrush(QBrush(color))

            self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def _reverse_connection_direction(self):
        """Reverse the direction of all selected connections."""
        connections_reversed = False
        for item in self.current_selection:
            if isinstance(item, ConnectionItem):
                item.reverse()
                connections_reversed = True

        # Update properties only if something was actually reversed
        if connections_reversed:
            self.update_properties(self.current_selection)

    def _open_external_references_dialog(self):
        """Open the dialog to manage external references for the selected Point."""
        # Check should be reliable now due to button visibility logic
        if len(self.current_selection) == 1 and isinstance(self.current_item, EntityItem) and isinstance(
                self.current_item.entity, Point):
            point_item = self.current_item
            dialog = ExternalReferencesDialog(point_item, self)
            dialog.exec_()  # Show modally
        else:
            # Fallback warning
            QMessageBox.warning(self, "Selection Error", "Please select a single Point entity to manage references.")


class EntityBrowser(QTreeWidget):
    """Tree-based browser for available entity types."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Entities")
        self.setDragEnabled(True)
        self._populate_entity_tree()

        # Expand all items in the tree
        self.expandAll()

    def _populate_entity_tree(self):
        """Load entities into the tree view organized by category."""
        entities = EntityLibrary.get_all_entities()

        # Track category paths with their tree items
        category_items = {}

        for entity in entities:
            current_path = ""
            parent_item = None

            # Process each category in the hierarchy
            for category in entity.category:
                # Build path
                if current_path:
                    current_path += "/" + category
                else:
                    current_path = category

                # Create category if it doesn't exist
                if current_path not in category_items:
                    category_tree_item = QTreeWidgetItem([category])

                    if parent_item:
                        parent_item.addChild(category_tree_item)
                    else:
                        self.addTopLevelItem(category_tree_item)

                    category_items[current_path] = category_tree_item

                # Update parent for next iteration
                parent_item = category_items[current_path]

            # Add entity as leaf node
            entity_item = QTreeWidgetItem([entity.name])
            entity_item.setData(0, Qt.UserRole, entity)

            # Create icon from SVG
            renderer = QSvgRenderer(QByteArray(entity.svg_data.encode()))
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            entity_item.setIcon(0, QIcon(pixmap))

            # Add to tree
            parent_item.addChild(entity_item)

    def mouseMoveEvent(self, event):
        """Handle drag start for entities."""
        if event.buttons() != Qt.LeftButton:
            return

        # Get selected item
        item = self.currentItem()
        if not item:
            return

        # Ensure it's an entity
        entity = item.data(0, Qt.UserRole)
        if not entity:
            return

        # Setup drag operation
        drag = QDrag(self)
        mime_data = QMimeData()

        # Store entity data
        mime_data.setText(entity.name)

        # Store SVG data
        svg_bytes = QByteArray(entity.svg_data.encode())
        mime_data.setData("application/entity-svg", svg_bytes)

        # Store URI
        uri_bytes = QByteArray(str(entity.uri_ref).encode())
        mime_data.setData("application/entity-uri", uri_bytes)

        drag.setMimeData(mime_data)

        # Execute drag
        drag.exec_(Qt.CopyAction)


class Canvas(QGraphicsView):
    """Interactive canvas for building system designs."""

    selection_changed = pyqtSignal(object)

    def __init__(self, properties_panel: PropertyPanel):

        super().__init__()

        self.scene: QGraphicsScene = QGraphicsScene(self)
        self.setScene(self.scene)

        # View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setAcceptDrops(True)

        # Setup grid
        self._draw_grid()

        # References
        self.property_panel = properties_panel

        # Connection creation state
        self.connection_in_progress = False
        self.temp_connection: ConnectionItem = None
        self.source_port = None

        # Panning attributes
        self.is_panning = False
        self.last_pan_point = None
        self.activated_panning = False
        self.hovered_port = None

        # Add state tracking for points visibility
        self.points_visible = True

        # Clipboard
        self.copied_items = []

        # Connect signals
        self.scene.selectionChanged.connect(self._handle_selection_changed)

        self.logger: Logger = Logger(self)

    def show_message(self, text: str):
        self.parent().statusBar().showMessage(text)

    def update_property_panel(self, items=None):
        """Update the property panel with selected item information."""

        if self.property_panel:
            self.property_panel.update_properties(items)

    def _handle_selection_changed(self):
        """Handle scene selection changes and update property panel once."""

        selected = self.scene.selectedItems()

        self.update_property_panel(selected)

    def _draw_grid(self):
        """Draw background grid lines."""

        grid_pen = QPen(QColor(230, 230, 230))
        grid_pen.setStyle(Qt.DotLine)

        # Use class variables for dimensions
        width, height = AppConfig.canvas_width, AppConfig.canvas_height

        # Horizontal grid lines
        for y in range(0, height, AppConfig.grid_size):
            self.scene.addLine(0, y, width, y, grid_pen)

        # Vertical grid lines
        for x in range(0, width, AppConfig.grid_size):
            self.scene.addLine(x, 0, x, height, grid_pen)

        # Add special line for Points
        point_line_pen = QPen(QColor(215, 215, 215), 2)
        point_line_y = AppConfig.get_point_line_height()
        self.scene.addLine(0, point_line_y, width, point_line_y, point_line_pen)

        # Draw black frame around the grid
        frame_pen = QPen(AppConfig.frame_color, AppConfig.frame_width)
        self.scene.addRect(QRectF(0, 0, width, height), frame_pen)

        # Set scene size
        self.scene.setSceneRect(0, 0, width, height)

        # Draw black frame around the grid
        frame_pen = QPen(AppConfig.frame_color, AppConfig.frame_width)
        self.scene.addRect(0, 0, AppConfig.canvas_width, AppConfig.canvas_height, frame_pen)

    def dragEnterEvent(self, event):
        """Handle drag enter events for entity creation."""
        if event.mimeData().hasFormat("application/entity-svg"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Handle drag move events for entity creation."""
        if event.mimeData().hasFormat("application/entity-svg"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events for entity creation."""
        if event.mimeData().hasFormat("application/entity-svg"):
            try:
                # Get entity URI from mime data
                uri_ref_str = event.mimeData().data("application/entity-uri").data().decode()

                # Create entity
                entity_item = EntityItem(uri_ref_str)

                # Calculate drop position
                pos = self.mapToScene(event.pos())

                # Get SVG dimensions for centering
                svg_width = entity_item.renderer.defaultSize().width()
                svg_height = entity_item.renderer.defaultSize().height()

                # Calculate center offset
                center_x = svg_width / 2
                center_y = svg_height / 2

                # Check if this is a Point entity
                is_point = isinstance(entity_item.entity, Point)

                # Snap X coordinate to grid
                # Subtract center_x to center entity on drop point
                x = round(pos.x() / AppConfig.grid_size) * AppConfig.grid_size - center_x

                # Set Y coordinate - enforce constraint for Points
                if is_point:
                    y = AppConfig.get_point_line_height() - center_y
                else:
                    # Subtract center_y to center entity on drop point
                    y = round(pos.y() / AppConfig.grid_size) * AppConfig.grid_size - center_y

                # Set position
                entity_item.setPos(x, y)

                # Now add to scene
                self.scene.addItem(entity_item)

                # Select the new entity
                self.scene.clearSelection()
                entity_item.setSelected(True)

                event.acceptProposedAction()

                # Update status
                self.show_message(f"Added {entity_item.entity.name} at ({x}, {y})")

            except Exception as e:
                self.logger.error(f"Error in drop event: {e}")
                self.show_message(f"Error adding item: {str(e)}")

    def _start_connection_creation(self, port_item, event):
        """Start creating a new connection from a port."""

        self.connection_in_progress = True
        self.source_port = port_item

        # Create temporary connection
        self.temp_connection = ConnectionItem(self.source_port)
        self.scene.addItem(self.temp_connection)

        # Set initial end position
        mouse_scene_pos = self.mapToScene(event.pos())
        self.temp_connection.set_current_end_pos(mouse_scene_pos)

        event.accept()

    def _finish_connection_creation(self, event):
        """Finalize connection creation on mouse release."""
        target_port = None
        # Get item under cursor
        item = self.itemAt(event.pos())

        # Check if target is a valid port
        if isinstance(item, PortItem) and item != self.source_port:
            target_port = item

        if self.hovered_port:
            # Reset the visual cue regardless of success/failure
            # self.hovered_port.setBrush(self.DEFAULT_PORT_BRUSH) # Old way
            self.hovered_port.setHovered(False)  # <--- Use new method
            self.hovered_port = None

        if target_port:  # Check if we found a valid target port earlier
            # Finalize connection
            self.temp_connection.set_target_port(target_port)  # Use the stored target_port

            # Example:
            source_entity = self.source_port.entity_item
            target_entity = target_port.entity_item
            source_is_point = isinstance(source_entity.entity, Point)
            target_is_point = isinstance(target_entity.entity, Point)

            if target_is_point:
                self.temp_connection.relationship_type = BRICK_RELATIONSHIPS["hasPoint"]
            if source_is_point:
                self.temp_connection.relationship_type = BRICK_RELATIONSHIPS["isPointOf"]

            self.show_message("Connection created")  # Or more specific message
            self.scene.clearSelection()
            self.temp_connection.setSelected(True)

        else:
            # Cancel connection
            if self.temp_connection:  # Check if temp_connection exists before removing
                self.scene.removeItem(self.temp_connection)
            self.show_message("Connection canceled")

        # Reset state
        self.connection_in_progress = False
        self.temp_connection = None
        self.source_port = None

        event.accept()

    def mousePressEvent(self, event):
        """Handle mouse press events for connection creation and selection."""

        # Get item under cursor
        item = self.itemAt(event.pos())

        # Check if starting a connection from a port
        if isinstance(item, PortItem) and event.button() == Qt.LeftButton:
            self._start_connection_creation(item, event)
            return

        # Pan on middle mouse button
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_point = event.pos()

            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

        # For other items, use default behavior
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for connection creation, dragging, and port hovering."""

        previously_hovered = self.hovered_port
        current_hover_target = None

        if self.connection_in_progress and self.temp_connection:
            item_under_cursor = self.itemAt(event.pos())
            if isinstance(item_under_cursor, PortItem) and item_under_cursor != self.source_port:
                current_hover_target = item_under_cursor

            if previously_hovered != current_hover_target:
                # Reset the previously hovered port (if any)
                if previously_hovered:
                    # previously_hovered.setBrush(self.DEFAULT_PORT_BRUSH) # Old way
                    previously_hovered.setHovered(False)

                # Highlight the new target port (if any)
                if current_hover_target:
                    # current_hover_target.setBrush(self.HOVER_PORT_BRUSH) # Old way
                    current_hover_target.setHovered(True)

                self.hovered_port = current_hover_target

        # Update temporary connection during creation
        if self.connection_in_progress and self.temp_connection:
            mouse_scene_pos = self.mapToScene(event.pos())
            self.temp_connection.set_current_end_pos(mouse_scene_pos)

        # Handle panning movement (keep this logic)
        if self.is_panning and self.last_pan_point:
            # Calculate delta movement
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()

            # Scroll the view by delta amount
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())

            event.accept()
            return  # Panning handled, return here

        # Accept event if we updated the temp connection
        if self.connection_in_progress:
            event.accept()
            return  # Temp connection update handled, return here

        # For other moves (like item dragging), use default behavior
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for connection creation and selection."""
        # Finalize connection creation
        if self.connection_in_progress and self.temp_connection and event.button() == Qt.LeftButton:
            self._finish_connection_creation(event)
            return

        # Pan on middle mouse button
        if event.button() == Qt.MiddleButton and self.is_panning:  # Added check for is_panning
            self.is_panning = False
            self.last_pan_point = None  # Reset last pan point
            self.setCursor(Qt.ArrowCursor)  # Restore cursor
            event.accept()
            return

        # For other releases, use default behavior
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events for adding joints to connections."""
        # Get item under cursor
        item = self.itemAt(event.pos())

        # Check if clicked on a connection
        if isinstance(item, ConnectionItem):
            # Get position in scene coordinates
            scene_pos = self.mapToScene(event.pos())

            # Add joint at this position
            joint = item.add_joint_at_point(scene_pos)

            # Select the joint
            self.scene.clearSelection()
            joint.setSelected(True)

            # Update status
            self.show_message(f"Added joint at ({scene_pos.x():.1f}, {scene_pos.y():.1f})")

            event.accept()
            return

        # For other double-clicks, use default behavior
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""

        # Check if Ctrl key is pressed for zooming
        if event.modifiers() == Qt.ControlModifier:
            # Calculate zoom factor
            factor = 1.1

            # Normalize the delta value for wheel scrolling
            delta = event.angleDelta().y() / 8  # Normalize to standard units (usually 120 for one step)

            if delta < 0:
                # Zoom out
                self.scale(1.0 / factor, 1.0 / factor)
                self.show_message("Zoom Out")

            else:
                # Zoom in
                self.scale(factor, factor)
                self.show_message("Zoom In")

            event.accept()
            return
        else:
            # If the Ctrl key is not pressed, call the parent method or perform other actions
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Handle key press events for various operations."""

        # Select all items
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.select_all()
            self.show_message("Selected All Items")
            event.accept()
            return

        # Show shortcuts
        if event.key() == Qt.Key_H:
            self.showShortcutTips()
            event.accept()
            return

        # Delete selected items
        if event.key() == Qt.Key_Delete:
            items_count = len(self.scene.selectedItems())
            if items_count > 0:
                self._delete_selected_items()
            event.accept()
            return

        # Rotate selected entities
        if event.key() == Qt.Key_R:
            selected_entities = [item for item in self.scene.selectedItems()
                                 if isinstance(item, EntityItem)]
            if selected_entities:
                self._rotate_selected_entities()
            event.accept()
            return

        # Copy selected items
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            selected_count = len(self.scene.selectedItems())
            if selected_count > 0:
                self._copy_selected_items()

            event.accept()
            return

        # Paste copied items
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            if self.copied_items:
                self._paste_copied_items()
                entity_count = len(self.copied_items.get('entities', {}))
            event.accept()
            return

        # Toggle Points visibility with P key
        if event.key() == Qt.Key_P:
            self.toggle_points_visibility()
            status = "Show" if self.points_visible else "Hide"
            event.accept()
            return

        # Zoom in with + key
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:  # Equal key often shares with Plus
            self.scale(1.1, 1.1)

            if hasattr(self, 'parent') and callable(self.parent) and self.parent():
                self.show_message("Zoomed in")
            event.accept()
            return

        # Zoom out with - key
        if event.key() == Qt.Key_Minus:
            self.scale(1 / 1.1, 1 / 1.1)

            if hasattr(self, 'parent') and callable(self.parent) and self.parent():
                self.show_message("Zoomed out")
            event.accept()
            return

        # For other keys, use default behavior
        super().keyPressEvent(event)

    def _rotate_selected_entities(self):
        """Rotate all selected entity items by 90 degrees."""
        selected_entities = [item for item in self.scene.selectedItems()
                             if isinstance(item, EntityItem)]

        if not selected_entities:
            return

        # Rotate each entity
        for entity in selected_entities:
            entity.rotate_90_degrees()

        # Property panel will update automatically due to selection

        self.show_message(f"Rotated {len(selected_entities)} entity(s) by 90°")

    def _delete_selected_items(self):
        """Delete all selected items from the scene."""
        selected_items = self.scene.selectedItems()

        if not selected_items:
            return

        # Create copy of the list since we'll be modifying it
        items_to_delete = selected_items.copy()

        for item in items_to_delete:
            if isinstance(item, ConnectionItem):
                # Handle connection removal
                item.remove()
            elif isinstance(item, EntityItem):
                # Remove all connected connections first
                connections = []
                if hasattr(item, 'port'):
                    connections = item.port.connections.copy()

                # Remove connections
                for connection in connections:
                    connection.remove()

                # Remove entity
                self.scene.removeItem(item)
            elif isinstance(item, JointItem):
                # Remove joint from connection
                if item.connection:
                    if item in item.connection.joints:
                        item.connection.joints.remove(item)

                    # Update connection
                    item.connection.update_position()

                    # Remove joint
                    self.scene.removeItem(item)
            else:
                # Remove other items
                self.scene.removeItem(item)

        # Property panel will update automatically due to selection change
        self.show_message(f"Deleted {len(items_to_delete)} item(s)")

    def _copy_selected_items(self):
        """Copy selected items to internal clipboard."""

        selected_items = self.scene.selectedItems()

        # Clear clipboard
        self.copied_items = []
        copied_entities = {}

        # First pass: copy selected entities
        for item in selected_items:
            if isinstance(item, EntityItem):
                # Store entity details
                original_id = id(item)
                copied_entities[original_id] = {
                    'entity': item.entity,
                    'pos': item.pos(),
                    'rotation': item.rotation_angle,
                    'original_item': item
                }

        # Check if anything to copy
        if not copied_entities:
            self.show_message("Nothing copied - at least one entity must be selected")
            return

        # Second pass: find connections between selected entities
        copied_connections = []

        for item in self.scene.items():
            if isinstance(item, ConnectionItem):
                # Get endpoints
                source_entity_item = item.source_port.entity_item if item.source_port else None
                target_entity_item = item.target_port.entity_item if item.target_port else None

                # Skip incomplete connections
                if not source_entity_item or not target_entity_item:
                    continue

                # Check if both endpoints are in copied entities
                source_id = id(source_entity_item)
                target_id = id(target_entity_item)

                if source_id in copied_entities and target_id in copied_entities:
                    # Copy connection details
                    copied_connections.append({
                        'source_id': source_id,
                        'target_id': target_id,
                        'relationship_type': item.relationship_type,
                        'color': item.pen().color(),
                        'style': item.pen().style(),
                        'width': item.pen().width(),
                        'joints': [joint.scenePos() for joint in item.joints]
                    })

        # Store everything in clipboard
        self.copied_items = {
            'entities': copied_entities,
            'connections': copied_connections
        }

        # Update status
        entity_count = len(copied_entities)
        connection_count = len(copied_connections)

        if entity_count > 0 or connection_count > 0:
            self.show_message(f"Copied {entity_count} entities and {connection_count} connections")
        else:
            self.show_message("Nothing to copy")

    def _paste_copied_items(self):
        """Paste previously copied items with offset."""
        if not self.copied_items or not isinstance(self.copied_items, dict):
            self.show_message("Nothing to paste")
            return

        # Get copied data
        copied_entities = self.copied_items.get('entities', {})
        copied_connections = self.copied_items.get('connections', [])

        if not copied_entities:
            self.show_message("No entities to paste")
            return

        # Clear current selection
        self.scene.clearSelection()

        # Apply offset for paste position
        offset_x = 50
        offset_y = 50

        # First create new entities
        new_entity_mapping = {}

        for original_id, item_data in copied_entities.items():
            # Create new entity with same type
            original_entity = item_data['entity']
            new_item = EntityItem(original_entity.uri_ref)

            # Check if point - enforce constraint
            is_point = isinstance(original_entity, Point)

            # Position with offset
            original_pos = item_data['pos']
            pos_x = original_pos.x() + offset_x
            if is_point:
                # Points always go on the line
                pos_y = AppConfig.get_point_line_height() - new_item.renderer.defaultSize().height() / 2

            else:
                # Other entities use regular offset
                pos_y = original_pos.y() + offset_y

            print(original_pos, (pos_x, pos_y))

            new_item.setPos(pos_x, pos_y)

            # Apply rotation if needed
            # In _paste_copied_items:
            if 'rotation' in item_data:
                rotation = item_data['rotation']
                new_item.apply_rotation(rotation)

            # Add to scene
            self.scene.addItem(new_item)

            # Select item
            new_item.setSelected(True)

            # Store in mapping
            new_entity_mapping[original_id] = new_item

        # Then create connections between new entities
        new_connections = []
        new_joints = []

        for conn_data in copied_connections:
            # Get source and target from mapping
            source_id = conn_data['source_id']
            target_id = conn_data['target_id']

            if source_id not in new_entity_mapping or target_id not in new_entity_mapping:
                continue

            # Get new entities
            source_item = new_entity_mapping[source_id]
            target_item = new_entity_mapping[target_id]

            # Create new connection
            connection = ConnectionItem(source_item.port, target_item.port)
            connection.set_relationship_type(conn_data['relationship_type'])

            # Set style
            pen = QPen(conn_data['color'], conn_data['width'], conn_data['style'])
            connection.setPen(pen)

            # Add joints
            for joint_pos in conn_data['joints']:
                # Apply offset to joint position
                new_pos = QPointF(joint_pos.x() + offset_x, joint_pos.y() + offset_y)
                joint = connection.add_joint_at_point(new_pos)

                # Track new joint
                new_joints.append(joint)

            # Add to scene
            self.scene.addItem(connection)

            # Select connection
            connection.setSelected(True)

            # Track new connection
            new_connections.append(connection)

        # Select all joints
        for joint in new_joints:
            joint.setSelected(True)

        # Property panel will update automatically due to selection change

        # Update status
        entity_count = len(new_entity_mapping)
        connection_count = len(new_connections)
        joint_count = len(new_joints)

        self.show_message(f"Pasted {entity_count} entities, {connection_count} connections, and {joint_count} joints")

    def toggle_points_visibility(self):
        """Toggle visibility of Point entities and their relationships."""
        self.points_visible = not self.points_visible

        for item in self.scene.items():
            # Hide/show Point entities
            if isinstance(item, EntityItem):
                if isinstance(item.entity, Point):
                    item.setVisible(self.points_visible)

            # Hide/show Point-related connections and their arrows
            elif isinstance(item, ConnectionItem):
                relation_type = item.relationship_type
                is_point_relation = (relation_type == rdflib.BRICK.hasPoint or relation_type == rdflib.BRICK.isPointOf)

                if is_point_relation:
                    # Hide/show the connection line
                    item.setVisible(self.points_visible)

                    # Hide/show all arrows for this connection
                    for arrow in item.arrows:
                        arrow.setVisible(self.points_visible)

        # Update status message
        status = "showing" if self.points_visible else "hiding"
        self.show_message(f"Now {status} Points and their relationships")

    def showShortcutTips(self):
        """Show a small window with shortcut tips."""
        tips = (
            "Shortcut Tips:\n"
            "  - H: Show this help window\n"
            "  - Ctrl + Scroll: Zoom In/Out\n"
            "  - Middle Mouse Button: Pan the canvas\n"
            "  - Delete: Delete selected items\n"
            "  - Ctrl+A: Select all items\n"
            "  - R: Rotate selected entities 90°\n"
            "  - Ctrl+C: Copy selected items\n"
            "  - Ctrl+V: Paste copied items\n"
            "  - P: Toggle Points visibility\n"
            "  - +/-: Zoom In/Out\n"
        )

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Shortcut Tips")
        msg.setText(tips)
        msg.exec_()

    def select_all(self):
        for item in self.scene.items():
            if isinstance(item, (EntityItem, ConnectionItem, JointItem)):
                item.setSelected(True)

    def save_to_turtle(self, file_path):
        """
        Save the current design to a Turtle file.

        Args:
            file_path: Path where the file will be saved
        """
        # Create a new RDF graph
        g = rdflib.Graph()

        # Create explicit URIRefs for our design properties
        bind_namespaces(g=g)

        # Store all entities
        for item in self.scene.items():

            # Process EntityItems
            if isinstance(item, EntityItem):
                # Add type triple
                g.add((item.instance_uri, rdflib.RDF.type, item.entity.uri_ref))

                # Add position information
                pos = item.pos()
                pos_node = rdflib.BNode()
                g.add((item.instance_uri, VISU.hasPosition, pos_node))
                g.add((pos_node, VISU.x, rdflib.Literal(float(pos.x()))))
                g.add((pos_node, VISU.y, rdflib.Literal(float(pos.y()))))

                # Add rotation information
                rotation_literal = rdflib.Literal(item.rotation_angle, datatype=rdflib.XSD.integer)
                g.add((item.instance_uri, VISU.rotation, rotation_literal))

                # Add label if it exists
                if item.label:
                    g.add(
                        (item.instance_uri, rdflib.RDFS.label, rdflib.Literal(item.label, datatype=rdflib.XSD.string)))

                if isinstance(item.entity, Point) and item.external_reference:
                    ref_data = item.external_reference  # Get the single dictionary
                    ref_node = BLDG[short_uuid()]  # Create a node for the reference details

                    g.add((item.instance_uri, BRICK_REF.hasExternalReference, ref_node))

                    ref_type = ref_data.get('type')
                    if ref_type == "BACnet":
                        g.add((ref_node, RDF.type, BRICK_REF.BACnetReference))
                        option = ref_data.get('option', 1)
                        # Store option explicitly? Optional, but could be helpful
                        # g.add((ref_node, VISU.bacnetOption, rdflib.Literal(option)))

                        # Option 1: Use specific BACnet properties
                        if option == 1:
                            if 'object-identifier' in ref_data:
                                g.add((ref_node, BACNET['object-identifier'],
                                       rdflib.Literal(ref_data['object-identifier'])))
                            if 'object-name' in ref_data:
                                g.add((ref_node, BACNET['object-name'], rdflib.Literal(ref_data['object-name'])))
                            if 'object-type' in ref_data:
                                g.add((ref_node, BACNET['object-type'], rdflib.Literal(ref_data['object-type'])))
                            # Use 'property-identifier' for saving if available
                            prop_id_key = 'property-identifier' if 'property-identifier' in ref_data else 'read-property'
                            if prop_id_key in ref_data:
                                g.add((ref_node, BACNET['property-identifier'],
                                       rdflib.Literal(ref_data[prop_id_key])))  # Save as property-identifier
                            if 'objectOf' in ref_data:  # Device ID stored as objectOf
                                g.add((ref_node, BACNET.objectOf,
                                       rdflib.Literal(ref_data['objectOf'])))  # Literal for now

                        # Option 2: Use BACnetURI
                        elif option == 2:
                            if 'BACnetURI' in ref_data:
                                g.add((ref_node, BRICK.BACnetURI, rdflib.Literal(ref_data['BACnetURI'])))
                            if 'objectOf' in ref_data:  # Device ID stored as objectOf
                                g.add((ref_node, BACNET.objectOf,
                                       rdflib.Literal(ref_data['objectOf'])))  # Literal for now

                    elif ref_type == "Timeseries":
                        g.add((ref_node, RDF.type, BRICK_REF.TimeseriesReference))
                        if 'timeseriesId' in ref_data:
                            g.add((ref_node, BRICK_REF.hasTimeseriesId, rdflib.Literal(ref_data['timeseriesId'])))
                        if 'storedAt' in ref_data:
                            # Assuming storedAt is a URI/IRI, save as URIRef if possible, else Literal
                            try:
                                stored_at_uri = rdflib.URIRef(ref_data['storedAt'])
                                g.add((ref_node, BRICK_REF.storedAt, stored_at_uri))
                            except:  # Handle invalid URIs if necessary
                                g.add((ref_node, BRICK_REF.storedAt, rdflib.Literal(ref_data['storedAt'])))

        # Store all connections
        for item in self.scene.items():
            if isinstance(item, ConnectionItem) and item.source_port and item.target_port:

                # Add the relationship triple
                source_uri = item.get_source_entity_uri()
                target_uri = item.get_target_entity_uri()

                if source_uri and target_uri:
                    # Store the relationship type
                    g.add((source_uri, item.relationship_type, target_uri))

                    # Store connection visual properties
                    g.add((item.instance_uri, rdflib.RDF.type, rdflib.URIRef(VISU.Connection)))
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "sourceEntity"), source_uri))
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "targetEntity"), target_uri))
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "relationshipType"), item.relationship_type))

                    # Store connection color
                    color = item.pen().color()
                    color_node = rdflib.BNode()
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "color"), color_node))
                    g.add((color_node, rdflib.URIRef(VISU + "red"),
                           rdflib.Literal(color.red(), datatype=rdflib.XSD.integer)))
                    g.add(
                        (color_node, rdflib.URIRef(VISU + "green"),
                         rdflib.Literal(color.green(), datatype=rdflib.XSD.integer)))
                    g.add((color_node, rdflib.URIRef(VISU + "blue"),
                           rdflib.Literal(color.blue(), datatype=rdflib.XSD.integer)))

                    # Store line style
                    pen_style = item.pen().style()
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "lineStyle"),
                           rdflib.Literal(int(pen_style), datatype=rdflib.XSD.integer)))

                    # Store line width
                    pen_width = item.pen().width()
                    g.add((item.instance_uri, rdflib.URIRef(VISU + "lineWidth"),
                           rdflib.Literal(pen_width, datatype=rdflib.XSD.integer)))

                    # Store joints - using explicit URIRefs to avoid the error
                    for i, joint in enumerate(item.joints):
                        joint_node = rdflib.BNode()
                        g.add((item.instance_uri, VISU.hasJoint, joint_node))
                        g.add((joint_node, VISU.jointIndex, rdflib.Literal(i, datatype=rdflib.XSD.integer)))

                        joint_pos = joint.scenePos()
                        g.add(
                            (joint_node, VISU.x, rdflib.Literal(float(joint_pos.x()), datatype=rdflib.XSD.float)))
                        g.add(
                            (joint_node, VISU.y, rdflib.Literal(float(joint_pos.y()), datatype=rdflib.XSD.float)))

        # Serialize to turtle format and save
        g.serialize(destination=file_path, format="turtle")
        return True

    def load_from_turtle(self, file_path):
        """
        Load a design from a Turtle file.

        Args:
            file_path: Path to the Turtle file to load
        """

        # Create a new RDF graph and parse the file
        g = rdflib.Graph()
        g.parse(file_path, format="turtle")

        self.import_from_graph(g)

    def load_from_ifc(self, file_path):

        g = extract_topology(file_path)

        self.import_from_graph(g=g)

    def import_from_graph(self, g: rdflib.Graph):
        print(f"Starting import_from_graph with {len(g)} triples")

        # Define design namespace explicitly as a string prefix

        print(f"Using design namespace: {VISU}")

        # Dictionary to keep track of loaded entities by URI
        loaded_entities = {}

        # First pass: Load all entities
        print("First pass: Loading entities...")
        entity_count = 0
        skipped_count = 0

        for subject, predicate, obj in g.triples((None, rdflib.RDF.type, None)):
            # Skip connections - we'll handle them in the second pass
            if obj == VISU.Connection:
                continue

            if not str(obj).startswith(str(BRICK)) and not str(obj).startswith(str(REC)):
                # Skip non-BRICK entities
                continue

            # Check if it's an entity type from our library
            try:
                # Create a new entity item
                entity_item = EntityItem(obj)
                print(f"Creating entity of type {obj}")

                # Set the instance URI to match the saved one
                entity_item.instance_uri = subject

                # Add to scene
                self.scene.addItem(entity_item)

                # Store in loaded entities dictionary
                loaded_entities[str(subject)] = entity_item
                entity_count += 1

            except AttributeError as e:
                # Not an entity in our library, skip it
                self.logger.warning(f"Skipping entity {obj} because {e}")
                print(f"Skipping entity {obj} because {e}")
                skipped_count += 1
                continue

        print(f"Loaded {entity_count} entities, skipped {skipped_count} entities")

        # Set entity properties
        print("Setting entity properties...")
        for entity_uri_str, entity_item in loaded_entities.items():
            print(f"Setting properties for entity: {entity_uri_str}")
            entity_uri = rdflib.URIRef(entity_uri_str)

            # Set position
            for pos_node in g.objects(subject=entity_uri, predicate=VISU.hasPosition):
                x = float(g.value(subject=pos_node, predicate=VISU.x, default=0))
                y = float(g.value(subject=pos_node, predicate=VISU.y, default=0))
                print(f"  - Setting position: ({x}, {y})")
                entity_item.setPos(x, y)

            # Set rotation
            rotation_val = g.value(entity_uri, VISU.rotation, default=0)
            if rotation_val:
                print(f"  - Setting rotation: {rotation_val}")
                entity_item.apply_rotation(int(rotation_val))

            # Set label
            label = g.value(entity_uri, rdflib.RDFS.label)
            if label:
                print(f"  - Setting label: {label}")
                entity_item.label = str(label)
        print("Loading external references...")
        # Query for points that have an external reference node
        ref_query = """
                  SELECT DISTINCT ?point_uri ?ref_node
                  WHERE {
                      ?point_uri ref:hasExternalReference ?ref_node .
                      # Optional: Add constraint if points must have a specific type
                      # ?point_uri rdf:type brick:Point .
                  }
               """
        qres_refs = g.query(ref_query, initNs={"ref": BRICK_REF, "brick": BRICK, "rdf": RDF})
        print(f"Found {len(list(qres_refs))} potential points with external references")
        qres_refs = g.query(ref_query, initNs={"ref": BRICK_REF, "brick": BRICK, "rdf": RDF})  # Re-run

        ref_count = 0
        for row in qres_refs:
            point_uri, ref_node = row
            # print(f"Processing reference link: {point_uri} -> {ref_node}")

            entity_item = loaded_entities.get(str(point_uri))
            if not entity_item or not hasattr(entity_item, 'entity') or not isinstance(entity_item.entity, Point):
                print(f"  - Skipping: Entity {point_uri} not loaded or not a Point type.")
                continue

            # --- Build the reference dictionary for this ref_node ---
            current_ref_data = {}
            ref_type_found = None

            # Get all properties of the reference node
            for pred, obj in g.predicate_objects(subject=ref_node):
                prop_local_name = pred.split('#')[-1].split('/')[-1]
                prop_value = str(obj)  # Default to string

                if pred == RDF.type:
                    if obj == BRICK_REF.BACnetReference:
                        ref_type_found = "BACnet"
                        current_ref_data['type'] = "BACnet"
                    elif obj == BRICK_REF.TimeseriesReference:
                        ref_type_found = "Timeseries"
                        current_ref_data['type'] = "Timeseries"
                    continue  # Don't store rdf:type as a generic property

                # --- Store specific properties based on known predicates ---
                # Timeseries
                if pred == BRICK_REF.hasTimeseriesId:
                    current_ref_data['timeseriesId'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "Timeseries"  # Infer type
                elif pred == BRICK_REF.storedAt:
                    current_ref_data['storedAt'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "Timeseries"  # Infer type

                # BACnet (Option 1 - specific properties)
                elif pred == BACNET['object-identifier']:
                    current_ref_data['object-identifier'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "BACnet"; current_ref_data['option'] = 1
                elif pred == BACNET['object-name']:
                    current_ref_data['object-name'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "BACnet"; current_ref_data['option'] = 1
                elif pred == BACNET['object-type']:
                    current_ref_data['object-type'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "BACnet"; current_ref_data['option'] = 1
                elif pred == BACNET['property-identifier']:  # Load preferred key
                    current_ref_data['property-identifier'] = prop_value
                    if not ref_type_found: current_ref_data['type'] = "BACnet"; current_ref_data['option'] = 1
                elif pred == BACNET['read-property']:  # Fallback for older saves
                    if 'property-identifier' not in current_ref_data:  # Only if preferred key isn't set
                        current_ref_data['property-identifier'] = prop_value  # Store as preferred key
                    if not ref_type_found: current_ref_data['type'] = "BACnet"; current_ref_data['option'] = 1
                elif pred == BACNET.objectOf:  # Used for Device ID in both options
                    current_ref_data['objectOf'] = prop_value
                    # Don't infer type solely based on objectOf, could be ambiguous
                    # If type is already BACnet, don't overwrite option based on this.

                # BACnet (Option 2 - URI)
                elif pred == BRICK.BACnetURI:
                    current_ref_data['BACnetURI'] = prop_value
                    current_ref_data['type'] = "BACnet"  # Definitely BACnet
                    current_ref_data['option'] = 2  # Definitely option 2

                # Add other specific predicates if needed...

                else:
                    # Store unknown properties? Maybe less important now.
                    # current_ref_data.setdefault('properties', {})[prop_local_name] = prop_value
                    pass

            # --- Finalize and attach the reference ---
            if 'type' in current_ref_data:
                # Determine BACnet option if not set explicitly by BACnetURI
                if current_ref_data['type'] == 'BACnet' and 'option' not in current_ref_data:
                    # If URI wasn't found, assume option 1 if identifier is present
                    if 'object-identifier' in current_ref_data or 'property-identifier' in current_ref_data:
                        current_ref_data['option'] = 1
                    else:
                        print(
                            f"  - Warning: BACnet ref for {point_uri} has no URI or identifiers. Cannot determine option.")
                        # Default to option 1 or skip? Skipping might be safer.
                        continue  # Skip this reference if option is ambiguous

                # Add internal ID (optional)
                current_ref_data['id'] = str(uuid.uuid4())

                # Attach the single reference
                print(f"  - Attaching reference ({current_ref_data['type']}) to entity {point_uri}")
                entity_item.set_external_reference(current_ref_data)
                ref_count += 1
            else:
                print(
                    f"  - Warning: Could not determine reference type for {ref_node} linked to {point_uri}. Skipping.")

        print(f"Loaded {ref_count} external references")

        # Track relationships that have been visually represented
        processed_relationships = set()

        # Second pass: Load connections that have visual representations
        print("Second pass: Loading visual connections...")
        visual_conn_count = 0

        for conn_uri in g.subjects(rdflib.RDF.type, VISU.Connection):
            print(f"Processing connection: {conn_uri}")

            # Get source and target
            source_uri = g.value(conn_uri, VISU.sourceEntity)
            target_uri = g.value(conn_uri, VISU.targetEntity)

            if not source_uri or not target_uri:
                print(f"  - Skipping: Missing source or target")
                continue

            print(f"  - Connection from {source_uri} to {target_uri}")

            # Get the entity items
            source_item = loaded_entities.get(str(source_uri))
            target_item = loaded_entities.get(str(target_uri))

            if not source_item or not target_item:
                print(f"  - Skipping: Source or target not in loaded entities")
                continue

            # Create connection
            connection = ConnectionItem(source_item.port, target_item.port)
            print(f"  - Created connection between ports")

            # Set connection URI
            connection.instance_uri = conn_uri

            # Set relationship type
            rel_type_str = g.value(conn_uri, rdflib.URIRef(VISU + "relationshipType"))
            if rel_type_str:
                print(f"  - Setting relationship type: {rel_type_str}")
                for rel_name, rel_uri in BRICK_RELATIONSHIPS.items():
                    if str(rel_uri) == str(rel_type_str):
                        connection.set_relationship_type(rel_uri)
                        print(f"  - Matched to known relationship: {rel_name}")
                        # Track this relationship as processed
                        processed_relationships.add((str(source_uri), str(rel_uri), str(target_uri)))
                        break

            # Set color
            for color_node in g.objects(conn_uri, rdflib.URIRef(VISU + "color")):
                red_val = g.value(color_node, VISU.red, default=0)
                green_val = g.value(color_node, VISU.green, default=0)
                blue_val = g.value(color_node, VISU.blue, default=0)

                # Convert to integers regardless of value
                red = int(red_val)
                green = int(green_val)
                blue = int(blue_val)

                color = QColor(red, green, blue)
                print(f"  - Setting color: RGB({red}, {green}, {blue})")

                # Set line style
                style_val = g.value(conn_uri, VISU.lineStyle)
                line_style_val = Qt.SolidLine
                if style_val:
                    line_style_val = Qt.PenStyle(int(style_val))
                    print(f"  - Setting line style: {line_style_val}")

                # Set line width
                width_val = g.value(conn_uri, VISU.lineWidth, default=2)
                width = int(width_val) if width_val else 2
                print(f"  - Setting line width: {width}")

                # Apply pen
                pen = QPen(color, width, line_style_val, Qt.RoundCap, Qt.RoundJoin)
                connection.setPen(pen)

            # Add to scene
            self.scene.addItem(connection)
            visual_conn_count += 1

            # Load joints
            joint_data = []
            joint_count = 0
            for joint_node in g.objects(conn_uri, rdflib.URIRef(VISU + "hasJoint")):
                idx_val = g.value(joint_node, VISU.jointIndex)
                x_val = g.value(joint_node, VISU.x)
                y_val = g.value(joint_node, VISU.y)

                if idx_val is not None and x_val is not None and y_val is not None:
                    idx = int(idx_val)
                    x = float(x_val)
                    y = float(y_val)
                    joint_data.append((idx, x, y))
                    joint_count += 1
                    print(f"  - Found joint #{idx} at ({x}, {y})")

            # Sort joints by index
            joint_data.sort(key=lambda d: d[0])
            print(f"  - Adding {joint_count} joints to connection")

            # Add joints to connection
            for _, x, y in joint_data:
                connection.add_joint_at_point(QPointF(x, y))

            # Update connection visuals
            connection.update_position()

        print(f"Added {visual_conn_count} visual connections")

        # Third pass: Create straight connections for relationships without visual elements
        print("Third pass: Creating implicit connections from relationships...")
        implicit_conn_count = 0

        for relation_uri in BRICK_RELATIONSHIPS.values():
            print(f"Checking for implicit {relation_uri} relationships...")
            for source_uri, _, target_uri in g.triples((None, relation_uri, None)):
                print(f"Found relationship: {source_uri} -> {target_uri}")

                # Skip if source or target is not a loaded entity
                if str(source_uri) not in loaded_entities or str(target_uri) not in loaded_entities:
                    print(f"  - Skipping: Source or target not loaded")
                    continue

                # Skip if this relationship is already processed
                if (str(source_uri), str(relation_uri), str(target_uri)) in processed_relationships:
                    print(f"  - Skipping: Relationship already represented visually")
                    continue

                # Get the entity items
                source_item = loaded_entities[str(source_uri)]
                target_item = loaded_entities[str(target_uri)]
                print(f"  - Creating implicit connection")

                # Create a straight connection
                connection = ConnectionItem(source_item.port, target_item.port)

                # Set relationship type
                connection.set_relationship_type(relation_uri)

                # Generate a new instance URI for this connection
                connection.instance_uri = rdflib.URIRef(f"{VISU}Connection_{len(processed_relationships)}")
                print(f"  - Assigned new URI: {connection.instance_uri}")

                # Use default visual settings
                pen = QPen(QColor(0, 0, 0), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                connection.setPen(pen)

                # Add to scene
                self.scene.addItem(connection)
                implicit_conn_count += 1

                # Update connection
                connection.update_position()

                # Add to processed set to avoid duplicates
                processed_relationships.add((str(source_uri), str(relation_uri), str(target_uri)))

        print(f"Added {implicit_conn_count} implicit connections")
        print(f"Total connections: {visual_conn_count + implicit_conn_count}")
        print("Import complete!")

        return True
