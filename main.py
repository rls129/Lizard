from PySide6.QtWidgets import QApplication
from ui import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VHDL Editor")
    window = MainWindow()
    app.exec()


main()