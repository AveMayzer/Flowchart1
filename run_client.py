
import sys
from PyQt6.QtWidgets import QApplication
from client.views.main_window         import MainWindow
from client.controllers.editor_controller import EditorController


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Flowchart Editor")

    window = MainWindow()
    window.controller = EditorController(window)  
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
