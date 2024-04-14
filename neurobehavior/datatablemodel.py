from PySide6.QtCore import Slot
from PySide6.QtCore import QAbstractTableModel
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtQml import QmlElement

import json

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class DataTableModel(QAbstractTableModel):
    def __init__(self,  parent=None):
        super().__init__(parent)
        self._data = []
        self._columns = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if self._data:
            row = self._data[0]
            nitem = len(self._data[0])
            if "index" in row:
                return nitem - 1
            else:
                return nitem
        else:
            return 0

    def parseColumns(self):
        if not self._data:
            return
        cols = [c for c in sorted(self._data[0]) if c != "index"]
        if "timestamp" in cols:
            self._columns = ["timestamp"] + [c for c in cols if c!= "timestamp"]
        else:
            self._columns = cols

    @Slot(str)
    def setData(self, jsonTblData):
        tblData = json.loads(jsonTblData)
        self.beginResetModel()
        self._data = tblData
        self.parseColumns()
        self.endResetModel()

    @Slot(str)
    def addRow(self, jsonRowData):
        rowData = json.loads(jsonRowData)
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(rowData)

        if not self._columns and len(rowData):
            self.parseColumns()
        self.endInsertRows()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        row = index.row()
        col = self._columns[index.column()]

        if role == Qt.DisplayRole:
            return self._data[row][col]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            return self._columns[section]
        elif orientation == Qt.Vertical:
            row = self._data[0]
            if "index" in row:
                return self._data[section]["index"]
            else:
                return section
