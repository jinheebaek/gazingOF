from PySide6.QtCore import Signal, Slot, Property
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex
from PySide6.QtQml import QmlElement

from neurobehavior.neurobehavior import Neurobehavior
from neurobehavior.session import Session
from neurobehavior.dbmodels import SessionModel

import math

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SessionListModel(QAbstractListModel):
    nameRole = Qt.UserRole + 1
    sessionRole = Qt.UserRole + 2
    statusRole = Qt.UserRole + 3
    descriptionRole = Qt.UserRole + 4

    appChanged = Signal()
    pageChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app = None
        self.sessions = []

        self._page = 1
        self._item_per_page = 10

        self.pageChanged.connect(self.loadSession)
        self.appChanged.connect(self.loadSession)

    def getApp(self):
        return self._app

    def setApp(self, app):
        if not app:
            return
        if self._app:
            self._app.sessionListChanged.disconnect(self.loadSession)
        self._app = app
        self._app.sessionListChanged.connect(self.loadSession)
        self.appChanged.emit()

    app = Property(Neurobehavior, getApp, setApp, notify=appChanged)

    def getPage(self):
        return self._page

    def setPage(self, page):
        with self.app.DB() as db, db.begin():
            nready = db.query(SessionModel).filter(
                SessionModel.status == "ready"
            ).count()
            nrunning = db.query(SessionModel).filter(
                SessionModel.status == "running"
            ).count()
            ncompleted = db.query(SessionModel).filter(
                SessionModel.status == "completed"
            ).count()

            npage = math.ceil(
                (nready + nrunning + ncompleted) / self._item_per_page
            )

            if page > npage:
                page = npage
            if page < 1:
                page = 1
        self._page = page
        self.pageChanged.emit()

    page = Property(int, getPage, setPage, notify=pageChanged)

    def loadSession(self):
        if not self.app:
            return
        with self.app.DB() as db, db.begin():
            db_sessions = []
            if self.page == 1:
                session_ready = db.query(SessionModel).filter(
                    SessionModel.status == "ready"
                ).order_by(SessionModel.name.desc()).all()

                session_running = db.query(SessionModel).filter(
                    SessionModel.status == "running"
                ).order_by(SessionModel.name.desc()).all()

                for ses in session_ready:
                    db_sessions.append(ses)
                for ses in session_running:
                    db_sessions.append(ses)

            if len(db_sessions) < self._item_per_page:
                session_completed = (
                    db.query(SessionModel)
                    .filter(SessionModel.status == "completed")
                    .order_by(SessionModel.name.desc())
                    .limit(self._item_per_page - len(db_sessions))
                    .offset((self.page - 1) * self._item_per_page -
                            (self.page > 1) * len(db_sessions))
                ).all()
                for ses in session_completed:
                    db_sessions.append(ses)

            self.beginResetModel()
            self.sessions = []
            for db_session in db_sessions:
                name = db_session.name
                if name in self.app.sessions:
                    self.sessions.append(self.app.sessions[name])
                else:
                    session = Session(self.app, {
                        "name": db_session.name,
                        "status": db_session.status,
                        "protocol": db_session.protocol_name,
                        "sessionParams": db_session.session_params,
                        "protocolParams": db_session.protocol_params,
                    })
                    session.statusChanged.connect(self.loadSession)
                    self.sessions.append(session)
                    if session.status != "compeleted":
                        self.app.loadSession(session)
            self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if index.isValid() and 0 <= row < self.rowCount():
            if role == SessionListModel.nameRole:
                return self.sessions[row].name
            if role == SessionListModel.sessionRole:
                return self.sessions[row]
            if role == SessionListModel.statusRole:
                return self.sessions[row].status
            if role == SessionListModel.descriptionRole:
                return self.sessions[row].getDescription("short")

    @Slot(Session, result=bool)
    def contains(self, session):
        if session in self.sessions:
            return True
        else:
            return False

    @Slot(Session, result=int)
    def findIndex(self, session):
        return self.sessions.index(session)

    @Slot(int, result=Session)
    def at(self, index):
        if (0 <= index < self.rowCount()):
            return self.sessions[index]

    def rowCount(self, parent=QModelIndex()):
        return len(self.sessions)

    def roleNames(self):
        return {
            SessionListModel.nameRole: b"name",
            SessionListModel.sessionRole: b"session",
            SessionListModel.statusRole: b"status",
            SessionListModel.descriptionRole: b"description",
        }
