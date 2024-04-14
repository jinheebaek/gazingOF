import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

Item {
    id: root
    property string text
    property int index
    property var tbar

    Connections {
        target: tbar
        function onCurrentIndexChanged(index) {
            if (tbar.currentIndex == index) {
                /* btn.color = "#aaaaaa" */
                /* btn.color = "#252526" */
                btn.color = "#1e1e1e"
            } else {
                /* btn.color = "#cccccc" */
                btn.color = "#333333"
            }
        }
    }

    Rectangle {
        id: btn
        anchors.fill: parent
        property int index: root.index
        /* color: index == 0 ? "#aaaaaa" : "#cccccc" */
        /* color: index == 0 ? "#252526" : "#333333" */
        color: index == 0 ? "#1e1e1e" : "#333333"
        /* border.width: 1 */

        Text {
            id: btn_txt
            anchors.fill: parent
            text: root.text
            /* color: "#cccccc" */
            color: Material.color(Material.Grey)
            rotation: 270
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {
                tabbar.currentIndex = root.index
            }
        }
    }
}
