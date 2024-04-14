import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import neurobehavior

Item {
    id: root

    property Neurobehavior app

    SectionChamberView {
        id: sectionChamberView
        height: parent.height
        app: root.app
        clip: true
    }

    SectionSessionList {
        id: sectionSessionList
        anchors.left: sectionChamberView.right
        width: 130
        height: parent.height
        spacing: 3
        /* model: app.sessionList */

        onSessionSelected: function (sessionData) {
            /* root.sessionSelected(sessionData); */
        }
    }

    SectionSessionCtrl {
        id: sectionSessionCtrl
        anchors.left: sectionSessionList.right
        width: parent.width - sectionChamberView.width - sectionSessionList.width
        height: 200
        app: root.app
    }

    SectionDataView {
        id: sectionDataView
        anchors.top: sectionSessionCtrl.bottom
        anchors.left: sectionSessionList.right
        anchors.leftMargin: 5
        width: parent.width - sectionChamberView.width - sectionSessionList.width
        height: parent.width - sectionSessionCtrl.height
        app: root.app
        clip: true
    }

}
