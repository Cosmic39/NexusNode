import sys

from PySide6.QtWidgets import QApplication

from nexusnode.ui.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("NexusNode Command Center")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
