import sys

from PyQt6 import QtWidgets

from dataviewer import DataViewer

def main() -> int:
    """Initializes the application and runs it.

    Returns:
        int: The exit status code.
    """

    # Initialize the App
    app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("FAMHP")
    app.setOrganizationDomain("famhp.net")
    app.setStyle("Fusion")

    # Initialize the main window
    mainwindow: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    dataviewer = DataViewer()
    dataviewer.selectFiles()

    centralwidget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    centralwidget.setLayout(layout)

    mainwindow.setCentralWidget(centralwidget)
    mainwindow.showMaximized()
    dataviewer.showMaximized()

    return sys.exit(app.exec())


if __name__ == '__main__':
    sys.exit(main())
