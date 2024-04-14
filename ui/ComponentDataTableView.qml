import QtQuick
import QtQuick.Controls
import neurobehavior

Item {
    id: root
    property DataTableModel table: DataTableModel {
        onRowsInserted: function(idx, first, last) {
            tableView.tableVerticalBar.setPosition(1 - tableView.tableVerticalBar.size);
        }
    }

    property int cellWidth: 75
    property int cellHeight: 25
    property int headerThickness: 30

    /* placeholder     */
    Rectangle {
        width: root.headerThickness
        height: root.headerThickness
        color: Material.color(Material.Teal)
    }

    HorizontalHeaderView {
        id: horizontalHeader
        height: root.headerThickness
        width: parent.width - root.headerThickness
        syncView: tableView
        anchors.left: tableView.left
        /* x: root.headerThickness */
        clip: true

        delegate: Rectangle {
            implicitWidth: root.cellWidth
            implicitHeight: root.headerThickness
            border.width: 0.5
            color: Material.color(Material.Blue)

            Text {
                anchors.fill: parent
                // width: parent.width
                // height: parent.height
                clip: true
                text: display
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    VerticalHeaderView {
        id: verticalHeader
        width: root.headerThickness
        height: parent.height - root.headerThickness
        syncView: tableView
        anchors.top: tableView.top
        /* y: root.headerThickness */
        clip: true

        delegate: Rectangle {
            implicitWidth: root.headerThickness
            implicitHeight: root.cellHeight
            border.width: 0.5
            color: Material.color(Material.Teal)

            Text {
                anchors.fill: parent
                // width: parent.width
                // height: parent.height
                clip: true
                text: display
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    TableView {
        id: tableView
        anchors.top: horizontalHeader.bottom
        anchors.left: verticalHeader.right
        /* x: root.headerThickness */
        /* y: root.headerThickness */
        width: parent.width - verticalHeader.width
        height: parent.height - horizontalHeader.height
        clip: true
        model: root.table
        delegate: dataDelegate

        /* boundsMovement: Flickable.StopAtBounds */
        /* boundsBehavior: Flickable.DragAndOvershootBounds */
        boundsBehavior: Flickable.StopAtBounds

        property alias tableVerticalBar: tableVerticalBar
        ScrollBar.vertical: ScrollBar {
            id: tableVerticalBar;
            policy:ScrollBar.AlwaysOff
        }

        Component {
            id: dataDelegate
            Rectangle {
                id: dataRow
                implicitWidth: root.cellWidth
                implicitHeight: root.cellHeight
                border.width: 0.5

                Text {
                    anchors.fill: parent
                    /* width: parent.width */
                    /* height: parent.height */
                    clip: true
                    text: display
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
