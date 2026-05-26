# src/app/shacl_dialogs.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTextEdit, QTabWidget,
    QWidget, QFileDialog, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt


class ShaclValidationReportDialog(QDialog):
    def __init__(self, validation_result, parent=None):
        super().__init__(parent)

        self.validation_result = validation_result

        self.setWindowTitle("SHACL Validation Report")
        self.resize(1000, 600)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if self.validation_result.conforms:
            summary_text = "Validation passed. The data conforms to the SHACL constraints."
        else:
            count = len(self.validation_result.violations)
            summary_text = f"Validation failed. Found {count} validation result(s)."

        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)

        if self.validation_result.conforms:
            summary_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            summary_label.setStyleSheet("font-weight: bold; color: darkred;")

        layout.addWidget(summary_label)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Severity",
            "Focus Node",
            "Path",
            "Value",
            "Message",
            "Source Shape",
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self._populate_table()

        table_layout.addWidget(self.table)
        tabs.addTab(table_tab, "Violations")

        # Raw report tab
        raw_tab = QWidget()
        raw_layout = QVBoxLayout(raw_tab)

        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setPlainText(self.validation_result.report_text)

        raw_layout.addWidget(self.raw_text)
        tabs.addTab(raw_tab, "Raw Report")

        # Buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self._save_report)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def _populate_table(self):
        violations = self.validation_result.violations

        self.table.setRowCount(len(violations))

        for row, violation in enumerate(violations):
            values = [
                violation.get("severity", ""),
                violation.get("focus_node", ""),
                violation.get("path", ""),
                violation.get("value", ""),
                violation.get("message", ""),
                violation.get("source_shape", ""),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def _save_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save SHACL Validation Report",
            "",
            "Text Files (*.txt);;Turtle Files (*.ttl)"
        )

        if not file_path:
            return

        try:
            if file_path.lower().endswith(".ttl"):
                self.validation_result.report_graph.serialize(
                    destination=file_path,
                    format="turtle"
                )
            else:
                if not file_path.lower().endswith(".txt"):
                    file_path += ".txt"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.validation_result.report_text)

            QMessageBox.information(
                self,
                "Report Saved",
                f"SHACL validation report saved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save report:\n{str(e)}"
            )