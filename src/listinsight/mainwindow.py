import sys
from qtpy import QtWidgets

from resources import qrc_resources
from listinsight import ListInsight


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        if sys.platform == "win32":
            fpath = r"C:/Users/debru/Documents/DEMO/ListInsight"
        else: 
            fpath = r"/home/devdev/Documents/DEMO/ListInsight"

        self.listinsight = ListInsight(fpath, "dummy", self)
        # self.listinsight.setShortlistfile('shortlist.json')
        # self.listinsight.setTaggedFile('tagged.json')

        self.setCentralWidget(self.listinsight)

