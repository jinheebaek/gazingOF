from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtCore import qDebug, qWarning
from PySide6.QtNetwork import QTcpServer, QHostAddress, QAbstractSocket


class ChamberServer(QObject):
    connected = Signal(str)
    disconnected = Signal(str)
    msgReceived = Signal(str, str, int)

    @Slot()
    def initialize(self):
        self.server = QTcpServer()
        self.sockets = {}

        qDebug("TCP server started")
        self.server.listen(QHostAddress.Any, 8989)
        self.server.newConnection.connect(self.newConnection)
        self.server.acceptError.connect(self.onError)

    @Slot()
    def stop(self):
        for k in self.sockets:
            sock = self.sockets[k]
            sock.disconnected.disconnect()
            sock.readyRead.disconnect()
            sock.close()
            sock.deleteLater()
        self.server.close()
        self.server.deleteLater()
        qDebug("TCP server stopped")

    def __getChambername(self, socket):
        ip = socket.peerAddress().toString()
        chamber_id = int(ip.split(".")[-1]) - 100
        # chamber_id = len(self.sockets) + 1
        chambername = "chamber{}".format(chamber_id)
        return chambername

    @Slot()
    def newConnection(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.setSocketOption(QAbstractSocket.KeepAliveOption, 1)

            chambername = self.__getChambername(socket)
            self.sockets[chambername] = socket

            socket.disconnected.connect(self.dropConnection)
            socket.readyRead.connect(self.readSocket)
            # socket.errorOccurred.connect(self.onError)
            qDebug("new connection with chamber " + chambername)
            self.connected.emit(chambername)

    @Slot(QAbstractSocket.SocketError)
    def onError(self, error):
        qDebug("Error")
        # qDebug(self.sender().errorString())
        qDebug(error)

    @Slot()
    def dropConnection(self):
        socket = self.sender()
        socket.disconnected.disconnect(self.dropConnection)
        socket.readyRead.disconnect(self.readSocket)
        chambername = self.__getChambername(socket)
        del self.sockets[chambername]
        socket.deleteLater()
        self.disconnected.emit(chambername)
        qDebug("connection with chamber {} dropped".format(chambername))

    @Slot()
    def readSocket(self):
        socket = self.sender()
        chambername = self.__getChambername(socket)

        while socket.canReadLine():
            msg = socket.readLine().data()
            if msg.endswith(b"\r\n"):
                msg = msg[:-2]
            # qDebug("cmbr {}, from socket: {}".format(chambername, msg))
            if msg.startswith(b'i'):
                msg = int.from_bytes(msg[1:], byteorder="little")
                self.msgReceived.emit(chambername, "input", msg)
            elif msg.startswith(b'o'):
                msg = int.from_bytes(msg[1:], byteorder="little")
                self.msgReceived.emit(chambername, "output", msg)
            # elif msg.startswith(b'c'):
            #     self.msgReceived.emit(chambername, "config", msg[1:].decode())
            # elif not msg.startswith(b'l'):
            #     qDebug("cmbr {}, from socket: {}".format(chambername, msg))

    @Slot(str, bytes)
    def sendMessage(self, chambername, msg):
        if chambername not in self.sockets:
            qDebug("No TCP socket for chamber {}".format(chambername))
            return

        socket = self.sockets[chambername]

        if not socket.isOpen():
            qDebug("TCP socket clsoed for chamber {}".format(chambername))
            return

        # qDebug("cmbr {}, to socket: {}".format(chambername, msg))
        socket.write(msg)
