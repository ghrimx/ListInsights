from dataclasses import dataclass
from qtpy import QtWidgets


@dataclass
class Filter:
    expr: str
    enabled: bool
    failed: bool


class FilterPane(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.filters: list[Filter] = []