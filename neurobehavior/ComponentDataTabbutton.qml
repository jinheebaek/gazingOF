import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import neurobehavior

Item {
    id: root
    height: 30
    width: btn_txt.contentWidth + 20

    property string name
    property int index
    property var tbar

    property color color_active: Material.color(Material.BlueGrey)
    property color color_inactive: Material.color(Material.Grey)

    Connections {
        target: tbar
        function onCurrentIndexChanged() {
            if (tbar.currentIndex == root.index) {
                btn.color = root.color_active
            } else {
                btn.color = root.color_inactive
            }
        }
    }

    Rectangle {
        id: btn
        anchors.fill: parent
        property int index: root.index
        color: index == 0 ? root.color_active : root.color_inactive
        border.width: 1

        Text {
            id: btn_txt
            anchors.fill: parent
            text: root.name
            color: "white"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {
                tbar.currentIndex = root.index
            }
        }
    }

}
