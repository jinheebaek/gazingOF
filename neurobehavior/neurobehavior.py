import os
import datetime
import json
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtCore import qDebug, qWarning
from PySide6.QtCore import QThread
from PySide6.QtCore import QStandardPaths
from PySide6.QtQml import QmlElement

from neurobehavior.session import Session
from neurobehavior.chamber import Chamber
# from neurobehavior.chamber_local import ChamberLocal
from neurobehavior.chamberserver import ChamberServer
from neurobehavior.videoctrl import VideoCtrl
from neurobehavior.dbmodels import Base, SessionModel, ChamberModel, DataModel
from neurobehavior.protocol import *
from neurobehavior.pulsepal import PulsePal

QML_IMPORT_NAME = "neurobehavior"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Neurobehavior(QObject):
    chamberCfgChanged = Signal()
    sessionListChanged = Signal()
    chamberStateChanged = Signal(str, list)
    dataUpdated = Signal(str, str, str)
    dataAppended = Signal(str, str, str)
    chamberListChanged = Signal()
    protocolListChanged = Signal()

    inputChanged = Signal(str, str, bool, arguments=["chamber", "channel", "value"])
    outputChanged = Signal(str, str, bool, arguments=["chamber", "channel", "value"])
    updateOutput = Signal(str, list)

    chamberStartSession = Signal(str, Session, type, dict)
    requestServerOutput = Signal(str, bytes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = {}

        db_file = "sqlite:///{}/neurobehavior.db".format(
            QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        )
        self.engine = create_engine(db_file)
        self.DB = sessionmaker(self.engine)

        if not os.path.exists(db_file.replace("sqlite:///", "")):
            db_dir = os.path.dirname(db_file.replace("sqlite:///", ""))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            Base.metadata.create_all(self.engine)

        self.chambers = {}
        self.chamberThreads = {}
        self.protocolSupported = {
            "OF": ProtocolOF
        }

        # self.chamberServerThread = QThread()
        # self.chamberServer = ChamberServer()
        # self.chamberServer.moveToThread(self.chamberServerThread)
        # self.chamberServer.connected.connect(self.chamberConnected)
        # self.chamberServer.disconnected.connect(self.chamberDisconnected)
        # # self.chamberServer.msgReceived.connect(self.chamberMsgReceived)
        # self.requestServerOutput.connect(self.chamberServer.sendMessage)
        # self.chamberServerThread.started.connect(self.chamberServer.initialize)
        # self.chamberServerThread.finished.connect(self.chamberServer.stop)
        # self.chamberServerThread.start()

        self.pp = PulsePal(self)

        self.addChamber({
            "name": "chamber1",
            "inputChannels": [""],
            "outputChannels": [""],
            "leds": [""]
        })

    @Slot()
    def stop(self):
        for session_name in self.sessions:
            session = self.sessions[session_name]
            if session.status == "running":
                session.stopSession()

        chambers = list(self.chambers.keys())
        for name in chambers:
            self.remove_chamber(name)

        # self.chamberServerThread.quit()
        # self.chamberServerThread.wait()

    @Slot(Session)
    def deleteSession(self, session):
        if session.status == "running":
            session.stopSession()

        with self.DB() as db, db.begin():
            try:
                db_session = db.query(SessionModel).filter(
                    SessionModel.name == session.name
                ).one()
                db.delete(db_session)
                db.commit()
            except:
                qWarning("session {} not found in DB".format(session.name))

        session.sessionDataChanged.disconnect(self.updateSessionDB)
        session.saveData.disconnect(self.saveData)
        del self.sessions[session.name]
        self.sessionListChanged.emit()

    @Property(list, notify=protocolListChanged)
    def protocolList(self):
        return list(sorted(self.protocolSupported.keys()))

    @Slot(bytes)
    def onArdOutputRequested(self, msg):
        cmbr = self.sender()
        self.requestServerOutput.emit(cmbr.name, msg)
        # self.chamberServer.sendMessage(cmbr.name, msg)

    def addChamber(self, configs):
        name = configs["name"]
        if name in self.chambers:
            return

        cmbrThread = QThread()
        cmbr = Chamber(configs)
        cmbr.moveToThread(cmbrThread)

        cmbr.inputChanged.connect(
            lambda ch, val: self.inputChanged.emit(cmbr.name, ch, val))
        cmbr.outputChanged.connect(
            lambda ch, val: self.outputChanged.emit(cmbr.name, ch, val))
        # cmbr.arduinoOutputRequested.connect(
        #     lambda msg: self.chamberServer.sendMessage(cmbr.name, msg)
        # )
        cmbr.arduinoOutputRequested.connect(self.onArdOutputRequested)

        cmbr.statusChanged.connect(
            self.chamberListChanged
        )
        cmbr.stateListChanged.connect(
            lambda s: self.chamberStateChanged.emit(cmbr.name, s)
        )
        cmbr.dataUpdated.connect(
            lambda tbl, rec: self.dataUpdated.emit(
                cmbr.name, tbl, json.dumps(rec))
        )
        cmbr.dataAppended.connect(
            lambda tbl, rec: self.dataAppended.emit(
                cmbr.name, tbl, json.dumps(rec))
            # self.dtest
        )
        cmbr.pulsepalTriggered.connect(self.pp.onPulsepalTriggered)
        cmbr.setPulsepalParams.connect(self.pp.setPulsepalParams)
        self.updateOutput.connect(cmbr.onUpdateOutputBroadcast)

        self.chamberStartSession.connect(cmbr.onSessionStartRequested)

        # self.chamberServer.msgReceived.connect(cmbr.onArdMsgReceived)

        cmbrThread.started.connect(cmbr.initialize)
        # cmbrThread.finished.connect(cmbr.stop)
        cmbrThread.start()

        cmbr.videoCtrl = VideoCtrl(self, int(name.lstrip("chamber")))
        cmbr.videoCtrl.gazingAngleUpdated.connect(cmbr.gazingAngleUpdated)

        self.chambers[name] = cmbr
        self.chamberThreads[name] = cmbrThread
        self.chamberListChanged.emit()

    def remove_chamber(self, name=None):
        if name not in self.chambers:
            return

        ## TODO status check
        cmbr = self.chambers.pop(name)
        cmbr.inputChanged.disconnect()
        cmbr.videoCtrl.stop()

        cmbrThread = self.chamberThreads.pop(name)
        cmbrThread.quit()
        cmbrThread.wait()

    # @Slot(str)
    # def chamberConnected(self, chambername):
    #     if chambername in self.chambers:
    #         cmbr = self.chambers[chambername]
    #         cmbr.onConnected()

    # @Slot(str)
    # def chamberDisconnected(self, chambername):
    #     if chambername in self.chambers:
    #         cmbr = self.chambers[chambername]
    #         cmbr.onDisconnected()

    # @Slot(str, str, int)
    # def chamberMsgReceived(self, chambername, msgtype, msg):
    #     # qDebug("msg received from chamber {}, type {}: {}".format(
    #     #     chambername, msgtype, msg))

    #     if chambername in self.chambers:
    #         cmbr = self.chambers[chambername]
    #         if msgtype == "input":
    #             cmbr.onArdInputChanged(msg)
    #         elif msgtype == "output":
    #             cmbr.onArdOutputChanged(msg)

    @Property(list, notify=chamberListChanged)
    def chamberList(self):
        chambers = []
        for cmbrname in sorted(self.chambers.keys()):
            cmbr = self.chambers[cmbrname]
            chambers.append({
                "name": cmbr.name,
                "status": cmbr.status,
                "inputChannels": cmbr.inputChannels,
                "outputChannels": cmbr.outputChannels,
                "chamber": cmbr
            })
        return chambers

    @Slot(Session, Chamber, result=str)
    def getData(self, session, chamber):
        if not session or not chamber:
            return json.dumps({})

        if session.status == "running":
            data = chamber.getData()
            return json.dumps(data)
        elif session.status == "completed":
            with self.DB() as db, db.begin():
                try:
                    data = db.execute(
                        select(DataModel.data)
                        .join(DataModel.session)
                        .join(DataModel.chamber)
                        .where(SessionModel.name == session.name)
                        .where(ChamberModel.name == chamber.name)
                    ).scalars().one()
                    return data
                except Exception:
                    qWarning("No data found for session {}, chamber {}".format(session.name, chamber.name))
        else:
            return json.dumps({})

    @Slot(Session, result=list)
    def getSessionChambers(self, session):
        with self.DB() as db, db.begin():
            try:
                db_session = db.query(SessionModel).filter(
                    SessionModel.name == session.name
                ).one()

                chambers = []
                for db_cmbr in db_session.chambers:
                    cmbr = self.chambers[db_cmbr.name]
                    chambers.append({
                        "name": db_cmbr.name,
                        "status": cmbr.status,
                        ## TODO load config stored in DB
                        "inputChannels": cmbr.inputChannels,
                        "outputChannels": cmbr.outputChannels,
                        "chamber": cmbr
                    })
                return chambers
            except:
                return []

    @Slot(str)
    def createSession(self, jsondata):
        data = json.loads(jsondata)
        if not data["subjects"]:
            return
        if not data["dataRoot"]:
            return

        session_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        protocol_data = data.pop("protocol")
        protocol_name = protocol_data["name"]
        # protocol_cls = self.protocolSupported[protocol_name]
        # protocol_params = protocol_data["params"]
        protocol_params = self.protocolSupported[protocol_name].params

        with self.DB() as db, db.begin():
            db_session = SessionModel(
                name=session_name,
                status="ready",
                session_params=data,
                protocol_name=protocol_name,
                protocol_params=protocol_params
            )
            chambers = []
            for cmbr_name in data["chambers"]:
                try:
                    db_chamber = db.query(ChamberModel).filter(
                        ChamberModel.name == cmbr_name
                    ).one()
                except:
                    db_chamber = ChamberModel(name = cmbr_name)
                chambers.append(db_chamber)
            db_session.chambers = chambers
            db.add(db_session)

            sessionData = {
                "name": db_session.name,
                "status": db_session.status,
                "protocol": db_session.protocol_name,
                "sessionParams": db_session.session_params,
                "protocolParams": db_session.protocol_params
            }

            db.commit()
            db.close()
            self.loadSession(Session(self, sessionData))
            self.sessionListChanged.emit()

    @Slot(Session)
    def loadSession(self, session):
        session.sessionDataChanged.connect(self.updateSessionDB)
        session.saveData.connect(self.saveData)
        self.sessions[session.name] = session

    @Slot(str)
    def updateSessionDB(self, sessionData):
        with self.DB() as db, db.begin():
            db_session = db.query(SessionModel).filter(
                SessionModel.name == sessionData["name"]
            ).one()
            db_session.status = sessionData["status"]
            db.commit()

    def saveData(self, session_name, chamber_name, sbj, data):
        with self.DB() as db, db.begin():
            db_session_id = db.query(SessionModel).filter(
                SessionModel.name == session_name
            ).one().id
            db_chamber_id = db.query(ChamberModel).filter(
                ChamberModel.name == chamber_name
            ).one().id

            db_data = DataModel(
                session_id=db_session_id,
                chamber_id=db_chamber_id,
                subject=sbj,
                data=data
            )
            db.add(db_data)
            db.commit()

    def makeDataPath(self, root, sessionName, subject, experiment=""):
        data_format = "hdf"

        if experiment:
            file_name_format = "{sname}_{sbj}-{experiment}"
            file_name = file_name_format.format(
                sname=sessionName, sbj=subject, experiment=experiment)
        else:
            file_name_format = "{sname}_{sbj}"
            file_name = file_name_format.format(sname=sessionName, sbj=subject)

        date = sessionName.split("_")[0]
        data_file = os.path.join(root, subject, date, file_name)

        if data_format == "hdf":
            return data_file + ".h5"

    # @Slot(str, str, str, result=bool)
    # def checkDataExists(self, root, sessionName, subject, experiment):
    #     path = self.makeDataPath(root, sessionName, subject, experiment)
    #     return os.path.exists(path)
