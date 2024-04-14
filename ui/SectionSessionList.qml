import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import neurobehavior

Item {
    id: root

    signal sessionSelected(session: Session)
    property Neurobehavior app
    property Session currSession
    property real spacing
    property real itemRadius: 0
    property real itemHeight: 60

    onSessionSelected: function(session) {
        root.currSession = session;
    }

    ListView {
        id: sessionList
        x: 10
        y: 10
        width: root.width - 10
        height: root.height - 10
        spacing: root.spacing

        model: SessionListModel {
            id: sessionListModel
            app: root.app
            onModelReset: {
                if (sessionListModel.rowCount() > 0) {
                    if (currSession && sessionListModel.contains(currSession)) {
                        let idx = sessionListModel.findIndex(currSession);
                        root.sessionSelected(sessionListModel.at(idx));
                    } else {
                        root.sessionSelected(sessionListModel.at(0));
                    }
                }
            }
        }
        delegate: sessionDelegate

        Component {
            id: sessionDelegate

            Item {
                id: sessionItem
                width: sessionList.width
                height: root.itemHeight

                Rectangle {
                    id: sessionInfo
                    width: parent.width - 10
                    height: parent.height
                    color: model.session.status == "running"? Material.color(Material.DeepOrange) :
                        (model.session.status == "ready"? Material.color(Material.Green) : "#eeeeee")
                    radius: root.itemRadius
                    clip: true

                    Text {
                        id: txtSessionName
                        width: parent.width
                        text: model.name
                        font.pointSize: 12
                        font.bold: true
                        color: model.session.status == "completed" ? "black" : "white"
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        id: txtSessionDesc
                        anchors.top: txtSessionName.bottom
                        width: parent.width
                        height: sessionItem.height - txtSessionName.height
                        text: model.description
                        font.pointSize: 10
                        color: model.session.status == "completed" ? "black" : "white"
                        horizontalAlignment: Text.AlignHCenter
                    }
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: function(mouse) {
                            if (mouse.button === Qt.LeftButton) {
                                root.sessionSelected(model.session);
                            } else if (mouse.button === Qt.RightButton) {
                                contextMenu.popup();
                            }
                        }

                        Menu {
                            id: contextMenu
                            MenuItem {
                                text: "Delete"
                                onTriggered: {
                                    app.deleteSession(model.session);
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    id: markCurrentItem
                    anchors.left: sessionInfo.right
                    width: 10
                    height: parent.height
                    color: ListView.isCurrentItem ? "#333333" : "#252526"
                }
            }
        }
    }
}
