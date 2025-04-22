import rdflib
import uuid

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QLabel, QStackedWidget,
    QWidget, QGroupBox, QRadioButton, QMessageBox
)
from PyQt5.QtCore import Qt

from src.app.items import EntityItem


REF = rdflib.Namespace("https://brickschema.org/schema/Brick/ref#")
BACNET = rdflib.Namespace("http://data.ashrae.org/bacnet/2020#")
BRICK = rdflib.Namespace("https://brickschema.org/schema/Brick#")


class AddEditReferenceDialog(QDialog):
    """Dialog to add or edit a single external reference."""

    def __init__(self, existing_ref=None, parent=None):
        super().__init__(parent)
        self.existing_ref = existing_ref
        self.setWindowTitle("Add/Edit External Reference" if not existing_ref else "Edit External Reference")

        self.layout = QVBoxLayout(self)

        # --- Type Selection ---
        self.type_combo = QComboBox()
        self.type_combo.addItem("BACnet", "BACnet")
        self.type_combo.addItem("Timeseries", "Timeseries")
        self.type_combo.currentIndexChanged.connect(self._update_form)
        self.layout.addWidget(QLabel("Reference Type:"))
        self.layout.addWidget(self.type_combo)

        # --- Stacked Widget for Forms ---
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # --- BACnet Form ---
        self.bacnet_widget = QWidget()
        bacnet_layout = QVBoxLayout(self.bacnet_widget)
        bacnet_layout.setContentsMargins(0, 0, 0, 0)

        # BACnet Options
        self.bacnet_option_group = QGroupBox("BACnet Format")
        bacnet_options_layout = QHBoxLayout()
        self.bacnet_option1_radio = QRadioButton("Option 1: Fields")
        self.bacnet_option2_radio = QRadioButton("Option 2: URI")
        self.bacnet_option1_radio.toggled.connect(self._update_bacnet_options)
        bacnet_options_layout.addWidget(self.bacnet_option1_radio)
        bacnet_options_layout.addWidget(self.bacnet_option2_radio)
        self.bacnet_option_group.setLayout(bacnet_options_layout)
        bacnet_layout.addWidget(self.bacnet_option_group)

        self.bacnet_option_stack = QStackedWidget()
        bacnet_layout.addWidget(self.bacnet_option_stack)

        # BACnet Option 1 Fields
        self.bacnet_opt1_widget = QWidget()
        bacnet_opt1_form = QFormLayout(self.bacnet_opt1_widget)
        self.bacnet_obj_id_edit = QLineEdit()
        self.bacnet_obj_name_edit = QLineEdit()
        self.bacnet_obj_type_edit = QLineEdit()  # Could be a combo eventually
        self.bacnet_desc_edit = QLineEdit()
        self.bacnet_prop_edit = QLineEdit()  # Default 'present-value'
        self.bacnet_prop_edit.setPlaceholderText("present-value (default)")
        self.bacnet_obj_of_edit = QLineEdit()  # Optional device link
        bacnet_opt1_form.addRow("Object Identifier:", self.bacnet_obj_id_edit)
        bacnet_opt1_form.addRow("Object Name:", self.bacnet_obj_name_edit)
        bacnet_opt1_form.addRow("Object Type:", self.bacnet_obj_type_edit)
        bacnet_opt1_form.addRow("Description:", self.bacnet_desc_edit)
        bacnet_opt1_form.addRow("Read Property:", self.bacnet_prop_edit)
        bacnet_opt1_form.addRow("Object Of (Device URI):", self.bacnet_obj_of_edit)
        self.bacnet_option_stack.addWidget(self.bacnet_opt1_widget)

        # BACnet Option 2 Fields
        self.bacnet_opt2_widget = QWidget()
        bacnet_opt2_form = QFormLayout(self.bacnet_opt2_widget)
        self.bacnet_uri_edit = QLineEdit()
        self.bacnet_uri_edit.setPlaceholderText("bacnet://<dev>/<obj>[/<prop>[/<idx>]]")
        self.bacnet_obj_of_edit_opt2 = QLineEdit()  # Optional device link (same logical field)
        bacnet_opt2_form.addRow("BACnet URI:", self.bacnet_uri_edit)
        bacnet_opt2_form.addRow("Object Of (Device URI):", self.bacnet_obj_of_edit_opt2)
        self.bacnet_option_stack.addWidget(self.bacnet_opt2_widget)

        self.stacked_widget.addWidget(self.bacnet_widget)

        # --- Timeseries Form ---
        self.timeseries_widget = QWidget()
        timeseries_form = QFormLayout(self.timeseries_widget)
        self.ts_id_edit = QLineEdit()
        self.ts_stored_at_edit = QLineEdit()  # URI
        timeseries_form.addRow("Timeseries ID:", self.ts_id_edit)
        timeseries_form.addRow("Stored At (URI):", self.ts_stored_at_edit)
        self.stacked_widget.addWidget(self.timeseries_widget)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # --- Initialization ---
        self.ref_data = None
        if self.existing_ref:
            self._load_existing_data()
        else:
            # Default selection
            self.bacnet_option1_radio.setChecked(True)
            self._update_form()  # Trigger initial form display

        self.setMinimumWidth(400)

    def _load_existing_data(self):
        ref_type = self.existing_ref.get("type")
        if ref_type == "BACnet":
            self.type_combo.setCurrentText("BACnet")
            option = self.existing_ref.get("option", 1)  # Default to option 1 if missing
            if option == 1:
                self.bacnet_option1_radio.setChecked(True)
                self.bacnet_obj_id_edit.setText(self.existing_ref.get("object-identifier", ""))
                self.bacnet_obj_name_edit.setText(self.existing_ref.get("object-name", ""))
                self.bacnet_obj_type_edit.setText(self.existing_ref.get("object-type", ""))
                self.bacnet_desc_edit.setText(self.existing_ref.get("description", ""))
                self.bacnet_prop_edit.setText(self.existing_ref.get("read-property", ""))
                self.bacnet_obj_of_edit.setText(self.existing_ref.get("objectOf", ""))
            elif option == 2:
                self.bacnet_option2_radio.setChecked(True)
                self.bacnet_uri_edit.setText(self.existing_ref.get("BACnetURI", ""))
                self.bacnet_obj_of_edit_opt2.setText(self.existing_ref.get("objectOf", ""))  # Load into correct field

        elif ref_type == "Timeseries":
            self.type_combo.setCurrentText("Timeseries")
            self.ts_id_edit.setText(self.existing_ref.get("timeseriesId", ""))
            self.ts_stored_at_edit.setText(self.existing_ref.get("storedAt", ""))

        self._update_form()  # Ensure correct form is visible

    def _update_form(self):
        selected_type = self.type_combo.currentData()
        if selected_type == "BACnet":
            self.stacked_widget.setCurrentWidget(self.bacnet_widget)
            self._update_bacnet_options()  # Update BACnet sub-options
        elif selected_type == "Timeseries":
            self.stacked_widget.setCurrentWidget(self.timeseries_widget)

    def _update_bacnet_options(self):
        if self.bacnet_option1_radio.isChecked():
            self.bacnet_option_stack.setCurrentWidget(self.bacnet_opt1_widget)
        elif self.bacnet_option2_radio.isChecked():
            self.bacnet_option_stack.setCurrentWidget(self.bacnet_opt2_widget)

    def accept(self):
        """Validate and gather data before closing."""
        data = {}
        selected_type = self.type_combo.currentData()
        data['type'] = selected_type
        data['id'] = self.existing_ref.get('id') if self.existing_ref else str(uuid.uuid4())  # Keep or generate ID

        if selected_type == "BACnet":
            if self.bacnet_option1_radio.isChecked():
                data['option'] = 1
                obj_id = self.bacnet_obj_id_edit.text().strip()
                if not obj_id:
                    QMessageBox.warning(self, "Input Error", "BACnet Object Identifier is required for Option 1.")
                    return
                data['object-identifier'] = obj_id
                data['object-name'] = self.bacnet_obj_name_edit.text().strip()
                data['object-type'] = self.bacnet_obj_type_edit.text().strip()
                data['description'] = self.bacnet_desc_edit.text().strip()
                read_prop = self.bacnet_prop_edit.text().strip()
                if read_prop:  # Only include if not empty (defaults to present-value in schema)
                    data['read-property'] = read_prop
                obj_of = self.bacnet_obj_of_edit.text().strip()
                if obj_of: data['objectOf'] = obj_of

            elif self.bacnet_option2_radio.isChecked():
                data['option'] = 2
                uri = self.bacnet_uri_edit.text().strip()
                if not uri or not uri.startswith("bacnet://"):
                    QMessageBox.warning(self, "Input Error",
                                        "A valid BACnet URI (starting with 'bacnet://') is required for Option 2.")
                    return
                data['BACnetURI'] = uri
                obj_of = self.bacnet_obj_of_edit_opt2.text().strip()  # Get from correct field
                if obj_of: data['objectOf'] = obj_of

        elif selected_type == "Timeseries":
            ts_id = self.ts_id_edit.text().strip()
            if not ts_id:
                QMessageBox.warning(self, "Input Error", "Timeseries ID is required.")
                return
            data['timeseriesId'] = ts_id
            stored_at = self.ts_stored_at_edit.text().strip()
            if stored_at:  # Technically optional in some contexts, but usually needed
                data['storedAt'] = stored_at

        self.ref_data = data
        super().accept()  # Call QDialog's accept

    def get_data(self):
        """Return the collected reference data."""
        return self.ref_data


class ExternalReferencesDialog(QDialog):
    """Dialog to manage the list of external references for a Point."""

    def __init__(self, point_item: EntityItem, parent=None):
        super().__init__(parent)
        self.point_item = point_item
        self.setWindowTitle(f"External References for {point_item.label or point_item.entity.name}")

        self.layout = QVBoxLayout(self)

        # List widget to display references
        self.ref_list_widget = QListWidget()
        self.ref_list_widget.itemDoubleClicked.connect(self._edit_reference)
        self.layout.addWidget(self.ref_list_widget)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add...")
        self.edit_button = QPushButton("Edit...")
        self.delete_button = QPushButton("Delete")
        self.close_button = QPushButton("Close")

        self.add_button.clicked.connect(self._add_reference)
        self.edit_button.clicked.connect(self._edit_reference)
        self.delete_button.clicked.connect(self._delete_reference)
        self.close_button.clicked.connect(self.accept)  # Close dialog

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)

        self._populate_list()
        self.setMinimumSize(500, 300)

    def _populate_list(self):
        """Fill the list widget with current references."""
        self.ref_list_widget.clear()
        for ref in self.point_item.external_references:
            item = QListWidgetItem(self._get_ref_display_text(ref))
            item.setData(Qt.UserRole, ref)  # Store the full dict
            self.ref_list_widget.addItem(item)

    def _get_ref_display_text(self, ref_data):
        """Generate a user-friendly string for the list."""
        ref_type = ref_data.get("type", "Unknown")
        details = ""
        if ref_type == "BACnet":
            option = ref_data.get("option", 0)
            if option == 1:
                details = f"BACnet (Fields): ID={ref_data.get('object-identifier', 'N/A')}"
            elif option == 2:
                details = f"BACnet (URI): {ref_data.get('BACnetURI', 'N/A')}"
            else:
                details = f"BACnet (Unknown Option)"
        elif ref_type == "Timeseries":
            details = f"Timeseries: ID={ref_data.get('timeseriesId', 'N/A')}"
        else:
            details = f"{ref_type}: ID={ref_data.get('id', 'N/A')}"
        return details

    def _add_reference(self):
        """Open the AddEdit dialog to create a new reference."""
        dialog = AddEditReferenceDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_ref_data = dialog.get_data()
            if new_ref_data:
                # Add a unique internal ID if needed (helps with editing/deleting)
                new_ref_data['id'] = str(uuid.uuid4())
                self.point_item.external_references.append(new_ref_data)
                self._populate_list()  # Refresh the list

    def _edit_reference(self):
        """Open the AddEdit dialog to modify the selected reference."""
        selected_item = self.ref_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a reference to edit.")
            return

        existing_ref_data = selected_item.data(Qt.UserRole)
        dialog = AddEditReferenceDialog(existing_ref=existing_ref_data, parent=self)

        if dialog.exec_() == QDialog.Accepted:
            updated_ref_data = dialog.get_data()
            if updated_ref_data:
                # Find and update the reference in the point_item's list
                ref_id_to_update = existing_ref_data.get('id')
                for i, ref in enumerate(self.point_item.external_references):
                    if ref.get('id') == ref_id_to_update:
                        self.point_item.external_references[i] = updated_ref_data
                        break
                self._populate_list()  # Refresh the list

    def _delete_reference(self):
        """Delete the selected reference."""
        selected_item = self.ref_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a reference to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this reference?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            ref_to_delete = selected_item.data(Qt.UserRole)
            ref_id_to_delete = ref_to_delete.get('id')

            # Remove by ID matching
            self.point_item.external_references = [
                ref for ref in self.point_item.external_references
                if ref.get('id') != ref_id_to_delete
            ]
            self._populate_list()  # Refresh the list
