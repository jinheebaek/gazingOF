import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import neurobehavior

Item {
    id: root

    signal chamberSelected(chamberData: var)
    property var model
    property real spacing
    property real itemRadius: 0
    property real itemHeight: 45

    onModelChanged: {
        if (model && model.length > 0) {
            chamberSelected(model[0]);
        }
    }

    function getStatusColor(status) {
        if (status == "disconnected")
            return Material.color(Material.Grey)
        else if (status == "ready")
            return Material.color(Material.Green)
        else if (status == "running")
            return Material.color(Material.Indigo)
        else
            return Material.color(Material.Grey)
    }

    ListView {
        id: chamberList
        anchors.topMargin: 10
        x: 10
        y: 10
        width: parent.width - 10
        height: parent.height - 10
        spacing: 3

        model: root.model
        delegate: chamberDelegate

        Component {
            id: chamberDelegate

            Item {
                id: chamberItem
                width: chamberList.width
                /* height: 60 */
                /* height: width / 3 */
                height: root.itemHeight

                Rectangle {
                    id: chamberInfo
                    width: parent.width - 10
                    height: parent.height
                    /* color: Material.color(Material.Green) */
                    color: root.getStatusColor(modelData.status)
                    radius: root.itemRadius

                    Text {
                        id: txtChamberName
                        width: parent.width
                        text: modelData.name
                        font.pointSize: 12
                        font.bold: true
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                    }
                /*     Text { */
                /*         id: txtChamberDesc */
                /*         anchors.top: txtChamberName.bottom */
                /*         width: parent.width */
                /*         height: chamberItem.height - txtChamberName.height */
                /*         text: modelData.desc_string */
                /*         font.pointSize: 10 */
                /*         color: "white" */
                /*         horizontalAlignment: Text.AlignHCenter */
                /*     } */

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            root.chamberSelected(modelData);
                        }
                    }
                }
                /* Rectangle { */
                /*     id: markCurrentItem */
                /*     anchors.left: chamberInfo.right */
                /*     width: 10 */
                /*     height: parent.height */
                /*     color: ListView.isCurrentItem ? "#333333" : "#252526" */
                /* } */
            }
        }
    }
}
