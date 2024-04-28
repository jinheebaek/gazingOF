import QtQuick
import QtQuick.Controls

Window {
    id: rootWindow
    width: 640
    height: 480
    visible: true
    title: qsTr("Stimulation window")

    Rectangle {
        id: dot_looming

        property real r: 0

        color: "black"
        width: r * 2
        height: r * 2
        radius : r
        anchors.centerIn: parent

        function trigger() {
            looming_stim.start()
        }

        SequentialAnimation {
            id: looming_stim
            loops: 1
            running: false

            NumberAnimation {
                target: dot_looming
                property: "r"
                from: 10; to: 300; duration: 250
            }
            PauseAnimation {
                duration: 500
            }
            PropertyAction {
                target: dot_looming
                property: "r"
                value: 0
            }
        }
    }

    Rectangle {
        id: dot_sweep
        property real r: 0

        color: "black"
        width: r * 2
        height: r * 2
        radius : r

        function trigger() {
            sweep_stim.start()
        }

        SequentialAnimation{
            id: sweep_stim
            loops: 1
            running: false
            PropertyAction {
                target: dot_sweep
                property: "r"
                value: 20
            }
            ParallelAnimation {
                NumberAnimation {
                    target: dot_sweep
                    property: "x"
                    from: 0
                    to: 600
                    duration: 250
                }
                NumberAnimation {
                    target: dot_sweep
                    property: "y"
                    from: 0
                    to: 450
                    duration: 250
                }
            }
            PropertyAction {
                target: dot_sweep
                property: "r"
                value: 0
            }
        }
    }
}
