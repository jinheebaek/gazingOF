import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
/* import Qt.labs.settings */
import QtCore

import neurobehavior

Item {
    id: root

    property Neurobehavior app
    property Session session

    onSessionChanged: {
        if (!session)
            return;
        var sessionName = session.name;
        sectionSessionCtrl.title = "Session - " + sessionName;
        sectionSessionCtrl.description = session.getDescription("long");
        sectionChamberList.model = app.getSessionChambers(session);
    }

    Connections {
        target: app
        function onChamberListChanged(cmbrList) {
            if (!session)
                return;
            sectionChamberList.model = app.getSessionChambers(session);
        }
    }

    SectionSessionCtrl {
        id: sectionSessionCtrl
        width: parent.width
        app: root.app
        session: root.session
    }

    Item {
        id: areaChamberList
        anchors.top: sectionSessionCtrl.bottom
        width: 130
        height: parent.height - sectionSessionCtrl.height
        clip: true

        SectionChamberList {
            id: sectionChamberList
            anchors.fill: parent
            itemRadius: 10
            itemHeight: 45
            onChamberSelected: function(chamberData) {
                sectionChamberView.chamber = chamberData["chamber"];
                sectionChamberView.name = chamberData["name"];
                sectionChamberView.status = chamberData["status"];
                sectionChamberView.inputChannels = chamberData["inputChannels"];
                sectionChamberView.outputChannels = chamberData["outputChannels"];
                sectionDataView.chamber = chamberData["chamber"];
            }
        }
    }

    SectionChamberView {
        id: sectionChamberView
        anchors.top: sectionSessionCtrl.bottom
        anchors.left: areaChamberList.right
        height: areaChamberList.height
        app: root.app
        clip: true
    }

    SectionDataView {
        id: sectionDataView
        anchors.top: sectionSessionCtrl.bottom
        anchors.left: sectionChamberView.right
        anchors.leftMargin: 5
        width: parent.width - areaChamberList.width - sectionChamberView.width
        height: sectionChamberView.height
        clip: true

        app: root.app
        session: root.session
    }
}
