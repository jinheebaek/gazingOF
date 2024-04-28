import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtMultimedia
import QtCore
import neurobehavior

Window {
    id: mainWindow
    width: 1600
    height: 900
    visible: true
    title: qsTr("Neurobehavior")
    color: "#1e1e1e"

    /* Material.theme: Material.Dark */
    Material.theme: Material.Light
    Material.accent: Material.Purple

    Neurobehavior {
        id: neurobehavior
    }

    Rectangle {
        id: tabbar
        width: 40
        height: parent.height
        anchors.left: parent.left
        /* color: "#eeeeee" */
        color: "#333333"

        property int currentIndex: 0

        Column {
            y: 40
            Tabbutton {
                id: tbar_session
                width: tabbar.width
                height: 100
                text: "Session"
                index: 0
                tbar: tabbar
            }
            Tabbutton {
                id: tbar_cmbr
                width: tabbar.width
                height: 100
                text: "Chamber"
                index: 1
                tbar: tabbar
            }
            Tabbutton {
                id: tbar_device
                width: tabbar.width
                height: 100
                text: "Settings"
                index: 2
                tbar: tabbar
            }
        }
    }

    Rectangle {
        id: side
        /* width: parent.width - tabbar.width - 640 */
        width: 200
        height: parent.height
        anchors.left: tabbar.right
        /* color: "#aaaaaa" */
        /* color: "#252526" */
        color: "#1e1e1e"

        StackLayout {
            currentIndex: tabbar.currentIndex
            /* width: side.width - 20 */
            width: side.width
            height: side.height - 20
            /* x: 10 */
            y: 10

            SideSessionList {
                id: sideSessionList
                app: neurobehavior
                onSessionSelected: function(session) {
                    pageSessionView.session = session
                }
                onCreateButtonClicked: {
                    popupNewSession.open()
                }
            }

            SideChamberList {
                id: sideChamberList
                app: neurobehavior
                onChamberSelected: function(chamberData) {
                }
            }
        }
    }

    Rectangle {
        id: mainPage
        /* width: parent.width - tabbar.width - side.width - 30 */
        width: parent.width - tabbar.width - side.width - 15
        height: parent.height - 30
        anchors.left: side.right
        /* anchors.leftMargin: 15 */
        y: 15
        color: "#252526"

        StackLayout {
            currentIndex: tabbar.currentIndex
            width: parent.width - 20
            height: parent.height - 20
            anchors.centerIn: parent

            PageSessionView {
                id: pageSessionView
                app: neurobehavior
            }

            /* PageChamberView { */
            /*     id: pageChamberView */
            /*     app: neurobehavior */
            /* } */
        }

        Popup {
            id: popupNewSession
            width: mainPage.width - 50
            height: mainPage.height - 50
            anchors.centerIn: parent
            focus: true

            background: Rectangle {
                color: "#363637"
            }

            PageNewSession {
                /* anchors.fill: parent */
                app: neurobehavior
                anchors.fill: parent
                onClose: {
                    popupNewSession.close()
                }
            }
        }
    }

    /* WindowVisualStim { */
    /*     id: stimWindow */
    /* } */

    Dialog {
        id: dialog_closing
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Yes | Dialog.No

        property bool closing: false

        Label {
            text: "Close window ?"
        }
        onAccepted: {
            dialog_closing.closing = true;
            neurobehavior.stop();
            mainWindow.close();
        }
    }

    onClosing: function(close) {
        close.accepted = dialog_closing.closing;
        onTriggered: dialog_closing.open();
    }

    Settings {
        /* property alias test: sessionctrl.test */
    }
}
