import QtQuick
import QtQuick.Controls

Item {
    id: rootitem
    width : 200
    height: 200

    property double resize_marker_len: 8
    property double border_width: 2
    property double x_max: 640 * 0.8 * 2
    property double y_max: 480
    property color color: "black"

    readonly property double m_ex: (rootitem.resize_marker_len - rootitem.border_width) / 2

    property double origX: 0
    property double origY: 0
    property double origW: 0
    property double origH: 0

    MouseArea {
        anchors.fill: parent
        drag {
            target: parent
            axis: Drag.XAndYAxis
            minimumX: 0
            minimumY: 0
            maximumX: rootitem.x_max - rootitem.width
            maximumY: rootitem.y_max - rootitem.height
        }
    }

    Rectangle {
        id: rect
        anchors.fill: parent
        color: "transparent"
        border.color: rootitem.color
        border.width: rootitem.border_width
    }
    Rectangle {
        id: marker_ul
        x: -rootitem.m_ex
        y: -rootitem.m_ex
        width: rootitem.resize_marker_len
        height: rootitem.resize_marker_len
        color: rootitem.color


        MouseArea {
            anchors.fill: parent
            drag {
                target: rootitem
                axis: Drag.XAndYAxis
                minimumX: 0
                minimumY: 0
                maximumX: rootitem.origX + rootitem.origW - rootitem.resize_marker_len - 5
                maximumY: rootitem.origY + rootitem.origH - rootitem.resize_marker_len - 5
            }
            HoverHandler {
                cursorShape: Qt.SizeFDiagCursor
            }
            onPressed: {
                rootitem.origX = rootitem.x
                rootitem.origY = rootitem.y
                rootitem.origW = rootitem.width
                rootitem.origH = rootitem.height
            }
            onPositionChanged: {
                if (drag.active) {
                    rootitem.width = rootitem.origW + (rootitem.origX - rootitem.x)
                    rootitem.height = rootitem.origH + (rootitem.origY - rootitem.y)
                }
            }
        }
    }
    Rectangle {
        id: marker_ur
        x: rootitem.width - rootitem.m_ex - rect.border.width
        y: -rootitem.m_ex
        width: rootitem.resize_marker_len
        height: rootitem.resize_marker_len
        color: rootitem.color

        MouseArea {
            anchors.fill: parent
            drag {
                target: rootitem
                axis: Drag.XAndYAxis
                minimumX: rootitem.origX - rootitem.origW + rootitem.resize_marker_len + 5
                minimumY: 0
                maximumX: rootitem.x_max - rootitem.origW
                maximumY: rootitem.origY + rootitem.origH - rootitem.resize_marker_len - 5
            }
            HoverHandler {
                cursorShape: Qt.SizeBDiagCursor
            }
            onPressed: {
                rootitem.origX = rootitem.x
                rootitem.origY = rootitem.y
                rootitem.origW = rootitem.width
                rootitem.origH = rootitem.height
            }
            onPositionChanged: {
                if (drag.active) {
                    rootitem.width = rootitem.origW + (rootitem.x - rootitem.origX)
                    rootitem.height = rootitem.origH + (rootitem.origY - rootitem.y)
                    rootitem.x = rootitem.origX
                }
            }
        }
    }
    Rectangle {
        id: marker_bl
        x: -rootitem.m_ex
        y: rootitem.height - rootitem.m_ex - rect.border.width
        width: rootitem.resize_marker_len
        height: rootitem.resize_marker_len
        color: rootitem.color

        MouseArea {
            anchors.fill: parent
            drag {
                target: rootitem
                axis: Drag.XAndYAxis
                minimumX: 0
                minimumY: rootitem.origY - rootitem.origH + rootitem.resize_marker_len + 5
                maximumX: rootitem.origX + rootitem.origW - rootitem.resize_marker_len - 5
                maximumY: rootitem.y_max - rootitem.origH
            }
            HoverHandler {
                cursorShape: Qt.SizeBDiagCursor
            }
            onPressed: {
                rootitem.origX = rootitem.x
                rootitem.origY = rootitem.y
                rootitem.origW = rootitem.width
                rootitem.origH = rootitem.height
            }
            onPositionChanged: {
                if (drag.active) {
                    rootitem.width = rootitem.origW + (rootitem.origX - rootitem.x)
                    rootitem.height = rootitem.origH + (rootitem.y - rootitem.origY)
                    rootitem.y = rootitem.origY
                }
            }
        }
    }
    Rectangle {
        id: marker_br
        x: rootitem.width - rootitem.m_ex - rect.border.width
        y: rootitem.height - rootitem.m_ex - rect.border.width
        width: rootitem.resize_marker_len
        height: rootitem.resize_marker_len
        color: rootitem.color

        MouseArea {
            anchors.fill: parent
            drag {
                target: rootitem
                axis: Drag.XAndYAxis
                minimumX: rootitem.origX - rootitem.origW + rootitem.resize_marker_len + 5
                minimumY: rootitem.origY - rootitem.origH + rootitem.resize_marker_len + 5
                maximumX: rootitem.x_max - rootitem.origW
                maximumY: rootitem.y_max - rootitem.origH
            }
            HoverHandler {
                cursorShape: Qt.SizeFDiagCursor
            }
            onPressed: {
                rootitem.origX = rootitem.x
                rootitem.origY = rootitem.y
                rootitem.origW = rootitem.width
                rootitem.origH = rootitem.height
            }
            onPositionChanged: {
                if (drag.active) {
                    rootitem.width = rootitem.origW + (rootitem.x - rootitem.origX)
                    rootitem.height = rootitem.origH + (rootitem.y - rootitem.origY)
                    rootitem.x = rootitem.origX
                    rootitem.y = rootitem.origY
                }
            }
        }
    }
}
