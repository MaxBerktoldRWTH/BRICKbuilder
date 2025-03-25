import sys
from PyQt5.QtWidgets import QApplication
from src.app.windows import DiagramApplication


if __name__ == "__main__":

    app = QApplication(sys.argv)
    diagram_app = DiagramApplication()
    diagram_app.show()
    sys.exit(app.exec_())

