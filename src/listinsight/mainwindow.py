from qtpy import QtWidgets

from resources import qrc_resources
from listinsight import ListInsight


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        self.listinsight = ListInsight("/home/devdev/Documents/DEMO", "dummy", self)
        # self.listinsight.setShortlistfile('shortlist.json')
        # self.listinsight.setTaggedFile('tagged.json')

        self.setCentralWidget(self.listinsight)
