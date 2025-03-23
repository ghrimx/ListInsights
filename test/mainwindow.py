from src.listinsight.qtpy import QtWidgets

from src.listinsight.resources import qrc_resources
from src.listinsight.listinsight import ListInsight


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        self.listinsight = ListInsight("C:/Users/debru/Documents/DEMO", "dummy", self)
        # self.listinsight.setShortlistfile('shortlist.json')
        # self.listinsight.setTaggedFile('tagged.json')

        self.setCentralWidget(self.listinsight)
