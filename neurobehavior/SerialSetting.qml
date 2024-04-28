import QtQuick
import QtQuick.Controls
/* import Qt.labs.settings */
import QtCore

import neurobehavior

Item {
    id: root

    property string pulsepal_port

    Text {
        id: txt_ppal
        width: parent.width
        height: 30

        text: "PulsePal: "
        font.pointSize: 12
        color: "black"
        maximumLineCount: 1
        horizontalAlignment: Text.AlignHLeft
    }

    SerialList {
        id: seriallist
    }

    ComboBox {
        id: cbox_ppal
        x: 5
        anchors.top: txt_ppal.bottom
        width: parent.width

        model: seriallist.portsList
        onActivated: {
            console.log(seriallist.ports[index])
        }
    }

    Text {
        id: txt_chambers
        width: parent.width
        height: 30
        anchors.top: cbox_ppal.bottom
        anchors.topMargin: 10

        text: "Chambers: "
        font.pointSize: 12
        color: "black"
        maximumLineCount: 1
        horizontalAlignment: Text.AlignHLeft
    }

    Settings {
        property alias pulsepal_port: root.pulsepal_port
    }
}
