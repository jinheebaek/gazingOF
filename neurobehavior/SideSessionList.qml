import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import neurobehavior

Item {
    id: root

    signal sessionSelected(session: Session)
    signal createButtonClicked()
    property Neurobehavior app

    Button {
        id: btnCreateSession
        x: 10
        width: parent.width - 20
        height: 30
        text: "+"

        Material.foreground: "white"
        Material.background: Material.Indigo

        onClicked: {
            root.createButtonClicked()
        }
    }

    SectionSessionList {
        id: sectionSessionList
        anchors.top: btnCreateSession.bottom
        width: parent.width
        height: parent.height - btnCreateSession.height
        spacing: 3
        app: root.app

        onSessionSelected: function (session) {
            root.sessionSelected(session);
        }
    }
}
