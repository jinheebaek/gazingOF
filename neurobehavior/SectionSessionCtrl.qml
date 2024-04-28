import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import neurobehavior

Item {
    id: root
    height: sectionTitle.height + txt_session_description.height + sectionCtrl.height + sectionProgressBar.height

    property string title: "Session"
    property string description: ""
    property Neurobehavior app
    property Session session

    Item {
        id: sectionTitle
        width: parent.width
        height: txtTitle.height + 10
        Text {
            id: txtTitle
            x: 15
            width: parent.width - 30

            text: root.title
            color: "white"
            font.pointSize: 18
        }
    }

    Text {
        id: txt_session_description
        anchors.top: sectionTitle.bottom
        anchors.topMargin: 10
        width: parent.width
        text: root.description
        color: "white"
        font.pointSize: 12
        wrapMode: Text.WordWrap
    }

    Item {
        id: sectionProgressBar
        anchors.top: txt_session_description.bottom
        anchors.topMargin: 5
        width: parent.width
        height: 25

        property real progress: root.session ? root.session.elapsedTime / root.session.duration : 0

        Rectangle {
            id: progressBar
            anchors.centerIn: parent
            width: parent.width - 25
            height: 8
            color: Material.color(Material.Grey)

            Rectangle {
                width: parent.width * Math.min(sectionProgressBar.progress, 1)
                height: parent.height
                color: Material.color(Material.Blue)
            }
        }
    }

    Item {
        anchors.top: sectionProgressBar.bottom
        anchors.right: sectionProgressBar.right
        anchors.topMargin: 5
        anchors.rightMargin: 20
        width: parent.width
        height: 5

        Text {
            anchors.fill: parent
            text: root.session ? Math.round(root.session.elapsedTime) + " / " + root.session.duration : 0
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            color: "white"
            font.pointSize: 15
        }
    }

    Item {
        id: sectionCtrl
        anchors.top: sectionProgressBar.bottom
        anchors.topMargin: 5
        width: parent.width
        height: 75

        Button {
            id: btn_ses_start
            x: 5
            Material.foreground: "white"
            Material.background: (session && session.status == "ready") ? Material.Blue : Material.BlueGrey

            text: "Start"

            /* function checkDataExists() { */
            /*     var chamber_subjects = session.getChamberSubjects(); */
            /*     var chambernames = Object.keys(chamber_subjects); */
            /*     for (var idx = 0; idx < chambernames.length; ++idx) { */
            /*         let chambername = chambernames[idx]; */
            /*         let subject = chamber_subjects[chambername]; */
            /*         /\* if (app.checkDataExists(session.dataRoot, chambername, subject)) *\/ */
            /*         if (app.checkDataExists(session.dataRoot, session.name, subject)) */
            /*             return true; */
            /*     } */
            /*     return false; */
            /* } */

            onClicked: {
                if (root.session.isDataExists())
                    dialog_forceoverwrite.open();
                else
                    root.session.startSession();
            }
        }

        Button {
            id: btn_ses_stop
            anchors.left: btn_ses_start.right
            anchors.top: btn_ses_start.top
            anchors.leftMargin: 5
            Material.foreground: "white"
            Material.background: (session && session.status == "running") ? Material.Red : Material.BlueGrey

            text: "Stop"
            onClicked: {
                root.session.stopSession();
            }
        }
    }

    Dialog {
        id: dialog_forceoverwrite
        anchors.centerIn: Overlay.overlay
        modal: true
        standardButtons: Dialog.Yes | Dialog.No

        Label {
            text: "Data file already exists. Overwrite ?"
        }
        onAccepted: {
            root.session.startSession();
        }
    }
}
