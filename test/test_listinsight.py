import sys
from src.listinsight.qtpy import QtWidgets

from test.mainwindow import MainWindow

from src.listinsight.utilities import config as mconf

def test_listinsight():
    assert main() == 0

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
    mainwindow: MainWindow= MainWindow()
    
    mainwindow.showMaximized()

    # return sys.exit(app.exec())
    return app.exec()


# if __name__ == '__main__':
#     sys.exit(main())

