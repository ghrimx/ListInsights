from qtpy import QtWidgets, QtCore
import json
from resources import qrc_resources
from dataviewer import DataViewer
from annotater import AnnotationModel, AnnotationDelegate

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow")

        self.dataviewer = DataViewer.setup("shortlist.json", "tagged.json")

        view = QtWidgets.QListView(self)
        model = AnnotationModel(view)

        view.setModel(model)
        delegate = AnnotationDelegate(view)
        view.setItemDelegate(delegate)

        json_path = QtCore.QFileInfo(__file__).absoluteDir().filePath("shortlist.json")

        with open(json_path) as file:
            document = json.load(file)
            model.load(document)

        self.setCentralWidget(view)

    def initUI(self):
        if self.dataviewer is None:
            return
        self.dataviewer.showMaximized()
