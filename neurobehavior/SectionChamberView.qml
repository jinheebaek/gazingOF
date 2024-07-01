import QtQuick
import QtQuick.Controls
import neurobehavior

Item {
    id: root

    property Neurobehavior app
    property Chamber chamber
    property var name
    property var status
    property var inputChannels
    property var outputChannels

    width: section_video.width

    Connections {
        target: app
        function onChamberStateChanged(cmbrname, statelist) {
            if (cmbrname === name) {
                stateList.model = statelist;
            }
        }
    }

    onChamberChanged: function() {
        if (root.chamber)
            stateList.model = root.chamber.stateList
    }

    Item {
        id: sectionTitle
        width: parent.width
        height: txtTitle.height + 10
        Text {
            id: txtTitle
            x: 15
            width: parent.width - 30

            text: "Chamber - " + root.name
            color: "white"
            font.pointSize: 18
        }
    }

    Item {
        id: section_video
        anchors.top: sectionTitle.bottom
        width: height * 640 * 0.8 * 2 / 480
        height: Math.min(parent.height * 0.5, 480)

        Rectangle {
            id: video_zone
            x: (parent.width - width) / 2
            color: "black"
            width: parent.width
            height: parent.height

            VideoViewItem {
                id: videoviewitem
                anchors.fill: parent
                // width: parent.width
                // height: parent.height

                chamber: root.chamber

        /*         /\* onPoseUpdated: { *\/ */
        /*         /\*     console.log(x) *\/ */
        /*         /\* } *\/ */

        /*         /\* ResizableRectangle { *\/ */
        /*         /\*     id: triggerzone *\/ */
        /*         /\*     x: 50 *\/ */
        /*         /\*     /\* y: 50 *\/ */
        /*         /\*     width : 200 *\/ */
        /*         /\*     height: 200 *\/ */
        /*         /\*     x_max: videoviewitem.width *\/ */
        /*         /\*     y_max: videoviewitem.height *\/ */
        /*         /\* } *\/ */
            }
        }
    }

    Item {
        id: section_ctrl

        anchors.top: section_video.bottom
        anchors.topMargin: 10
        width: section_video.width
        height: parent.height - section_video.height - sectionTitle.height

        Text {
            id: txt_input
            text: "Input"
            color: "white"
            font.pointSize: 13
        }

        ListView {
            id: inputList
            anchors.top: txt_input.bottom
            anchors.topMargin: 10
            width: parent.width
            height: 40
            spacing: 3
            orientation: Qt.Horizontal

            Component {
                id: inputDelegate
                Rectangle {
                    id: inputChannel
                    /* width: Math.min(40, inputInfo.width) */
                    width: Math.max(45, inputInfo.contentWidth + 10)
                    height: 40
                    border.width: 2
                    radius: 15
                    /* color: Material.color(Material.Grey) */
                    color: "#333333"

                    Text {
                        id: inputInfo
                        width: parent.width
                        height: parent.height
                        text: modelData
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    function updateColor() {
                        if (root.chamber && root.chamber.inputVals[index])
                            inputChannel.color = Material.color(Material.Red);
                        else
                            inputChannel.color = "#333333"
                    }

                    Connections {
                        target: root.app
                        function onInputChanged(chamber, channel, val) {
                            if (chamber == name && channel === modelData) {
                                updateColor();
                            }
                        }
                    }

                    Connections {
                        target: root
                        function onChamberChanged() {
                            updateColor();
                        }
                    }
                }
            }

            model: root.inputChannels
            delegate: inputDelegate
            /* focus: true */
        }

        Text {
            id: txt_output
            anchors.top: inputList.bottom
            anchors.topMargin: 15
            text: "Output"
            color: "white"
            font.pointSize: 13
        }

        Item {
            anchors.right: parent.right
            anchors.top: txt_output.top
            height: txt_output.contentHeight
            width: 300

            Rectangle {
                id: btn_clear_output
                width: 100
                anchors.right: btn_clear_led.left
                anchors.rightMargin: 10
                height: parent.height + 10
                y: -5
                border.width: 2
                radius: 10
                /* color: "white" */
                color: Material.color(Material.BlueGrey);
                Text {
                    width: parent.width
                    height: parent.height
                    color: "black"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: "Clear Output"
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        btn_clear_output.color = "white";
                    }
                    onExited: {
                        btn_clear_output.color = Material.color(Material.BlueGrey);
                    }
                    onPressed: {
                        btn_clear_output.color = Material.color(Material.Blue);
                    }
                    onReleased: {
                        btn_clear_output.color = "white";
                    }
                    onClicked: {
                        root.chamber.clearOutput();
                    }
                }
            }

            Rectangle {
                id: btn_clear_led
                anchors.right: parent.right
                width: 80
                height: parent.height + 10
                y: -5
                border.width: 2
                radius: 10
                /* color: "white" */
                color: Material.color(Material.BlueGrey);
                Text {
                    width: parent.width
                    height: parent.height
                    color: "black"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: "Clear LED"
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        btn_clear_led.color = "white";
                    }
                    onExited: {
                        btn_clear_led.color = Material.color(Material.BlueGrey);
                    }
                    onPressed: {
                        btn_clear_led.color = Material.color(Material.Blue);
                    }
                    onReleased: {
                        btn_clear_led.color = "white";
                    }
                    onClicked: {
                        root.chamber.clearLED();
                    }
                }
            }
        }

        ListView {
            id: outputList
            anchors.top: txt_output.bottom
            anchors.topMargin: 10
            width: parent.width
            height: 40
            spacing: 3
            orientation: Qt.Horizontal

            Component {
                id: outputDelegate
                Rectangle {
                    id: outputChannel
                    /* width: Math.min(40, outputInfo.width) */
                    width: Math.max(45, outputInfo.contentWidth + 10)
                    height: 40
                    border.width: 2
                    radius: 15
                    /* color: Material.color(Material.Grey) */
                    color: "#333333"

                    Text {
                        id: outputInfo
                        width: parent.width
                        height: parent.height
                        text: modelData
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    function updateColor() {
                        if (root.chamber &&root.chamber.outputVals[index])
                            outputChannel.color = Material.color(Material.Red);
                        else
                            outputChannel.color = "#333333"
                    }

                    Connections {
                        target: root.app
                        function onOutputChanged(chamber, channel, val) {
                            if (chamber == name && channel === modelData) {
                                updateColor();
                            }
                        }
                    }

                    Connections {
                        target: root
                        function onChamberChanged() {
                            updateColor();
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            app.updateOutput(name,
                                             [[modelData, !root.chamber.outputVals[index]]]);
                        }
                    }
                }
            }

            model: root.outputChannels
            delegate: outputDelegate
            /* focus: true */
        }

        Text {
            id: txt_states
            anchors.top: outputList.bottom
            anchors.topMargin: 15
            text: "State"
            color: "white"
            font.pointSize: 13
        }

        ListView {
            id: stateList
            anchors.top: txt_states.bottom
            anchors.topMargin: 10
            width: parent.width
            height: 40
            spacing: 3
            orientation: Qt.Horizontal

            delegate: stateDelegate

            Component {
                id: stateDelegate
                Rectangle {
                    id: stateItem
                    width: Math.max(45, stateInfo.contentWidth + 10)
                    height: 40
                    border.width: 2
                    radius: 15
                    color: Material.color(Material.Blue)

                    Text {
                        id: stateInfo
                        width: parent.width
                        height: parent.height
                        text: modelData
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
