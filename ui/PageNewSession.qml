import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Controls.Material
import QtCore
import neurobehavior

Item {
    id: root
    property color color
    property Neurobehavior app

    property url dataRoot
    property string protocolName

    signal createSessionRequested(var params)
    signal close()

    Component.onCompleted: {
        dataRoot = folderDialog.currentFolder
    }

    Item {
        width: parent.width - 40
        height: parent.height - 40
        anchors.centerIn: parent

        Text {
            id: txt_title
            text: "New Session"
            color: "white"
            font.pointSize: 18
            padding: 10
        }
        Text {
            id: txt_section_root
            anchors.top: txt_title.bottom
            anchors.topMargin: 10
            text: "Data root"
            color: "white"
            font.pointSize: 12
        }

        Item {
            id: section_root
            height: btn_data_dir.height
            anchors.top: txt_section_root.bottom

            Button {
                id: btn_data_dir
                x: 5
                text: "Dir"
                onClicked: {
                    folderDialog.open();
                }
            }
            Text {
                id: txt_data_root
                /* width: parent.width - btn_data_dir.width */
                width: 500
                height: btn_data_dir.height
                anchors.left: btn_data_dir.right
                anchors.leftMargin: 5

                text: folderDialog.currentFolder
                font.pointSize: 12
                color: "white"
                elide: Text.ElideLeft
                maximumLineCount: 1
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            id: txt_section_chambers
            anchors.top: section_root.bottom
            anchors.topMargin: 10
            /* topPadding: 10 */
            text: "Subjects"
            color: "white"
            font.pointSize: 12
        }

        Item {
            id: section_chambers
            width: parent.width
            /* height: 60 */
            height: chamber_list_view.contentHeight
            anchors.top: txt_section_chambers.bottom

            GridView {
                id: chamber_list_view
                x: 15
                width: parent.width - 15
                /* height: 200 */
                height: 600
                cellWidth: 350
                cellHeight: 50

                property var chambers: []
                property var subjects: []
                property var experiments: []

                onModelChanged: {
                    chambers = []
                    for (var idx = 0; idx < model.length; ++idx) {
                        chambers.push(model[idx].name)
                    }
                    subjects = []
                    experiments = []
                }

                Component {
                    id: chamberDelegate

                    Item {
                        id: chamberItem
                        width: chamber_list_view.cellWidth - 10
                        height: chamber_list_view.cellHeight - 10

                        /* property string sbj */
                        /* property string exp: "" */
                        /* property string cmbr: modelData.name */

                        Rectangle {
                            id: chamberName
                            width: parent.width * 2 / 8
                            height: parent.height
                            color: Material.color(Material.Green)
                            /* color: ListView.isCurrentItem ? "black" : "red" */

                            Text {
                                anchors.fill: parent
                                id: txt_chambername
                                text: modelData.name
                                color: "white"
                                font.pointSize: 11
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                        Rectangle {
                            id: subject
                            width: parent.width * 3 / 8
                            height: parent.height
                            anchors.left: chamberName.right
                            border.width: 0.5

                            TextField {
                                id: txtfield_sbj
                                x: 2
                                y: 4
                                width: parent.width - 4
                                height: parent.height
                                color: "black"
                                placeholderText: "Subject name"
                                placeholderTextColor: "#777777"
                                font.pointSize: 11
                                verticalAlignment: TextInput.AlignVCenter

                                onEditingFinished: {
                                    /* chamberItem.sbj = text */
                                    chamber_list_view.subjects[index] = text
                                }

                                Connections {
                                    target: root
                                    function onVisibleChanged() {
                                        if (root.visible)
                                            txtfield_sbj.forceActiveFocus();
                                    }
                                }
                            }
                        }
                        Rectangle {
                            id: experiment
                            width: parent.width * 3 / 8
                            height: parent.height
                            anchors.left: subject.right
                            border.width: 0.5

                            TextField {
                                id: txtfield_exp
                                x: 2
                                y: 4
                                width: parent.width - 4
                                height: parent.height
                                color: "black"
                                placeholderText: "(optional) experiment"
                                placeholderTextColor: "#777777"
                                font.pointSize: 11
                                verticalAlignment: TextInput.AlignVCenter

                                onEditingFinished: {
                                    /* chamberItem.exp = text */
                                    chamber_list_view.experiments[index] = text
                                }

                                Connections {
                                    target: root
                                    function onVisibleChanged() {
                                        if (root.visible)
                                            txtfield_exp.forceActiveFocus();
                                    }
                                }
                            }
                        }
                    }
                }

                model: app ? app.chamberList : null
                delegate: chamberDelegate
                /* focus: true */
            }
        }

        Text {
            id: txt_section_protocol
            anchors.top: section_chambers.bottom
            anchors.topMargin: 10
            /* topPadding: 10 */
            text: "Protocol"
            color: "white"
            font.pointSize: 12
        }
        Item {
            id: section_protocol
            anchors.top: txt_section_protocol.bottom

            ComboBox {
                id: cbox_prtc
                /* x: 5 */
                /* anchors.top: txt_prtc.bottom */
                width: 300

                property string lastProtocolMade

                model: app ? app.protocolList : null
                onActivated: {
                    /* protocol list will not change during running (unnotifyable) */
                    if (currentValue)
                        root.protocolName = currentValue;
                }
                Component.onCompleted: {
                    if (count > 0) {
                        if (cbox_prtc.model.includes(cbox_prtc.currentValue)) {
                            let idx = cbox_prtc.model.indexOf(cbox_prtc.lastProtocolMade);
                            cbox_prtc.currentIndex = idx;
                            cbox_prtc.activated(idx);
                        } else {
                            cbox_prtc.activated(0);
                        }
                    }
                }
            }
        }

        Button {
            id: btn_create
            x: 5
            y: parent.height - height - 5
            text: "Create Session"
            Material.foreground: "white"
            Material.background: Material.Blue

            function urlToString(url) {
                var s = url.toString();
                if (s.startsWith("file:///")) {
                    var k = s.charAt(9) === ':' ? 8 : 7;
                    return s.substring(k);
                } else {
                    return s;
                }
            }

            function createSession() {
                var chambers;
                var subjects;
                var experiments;
                [chambers, subjects, experiments] = getChambers();

                if (chambers) {
                    cbox_prtc.lastProtocolMade = cbox_prtc.currentValue;
                    app.createSession(JSON.stringify({
                        "dataRoot": urlToString(root.dataRoot),
                        "chambers": chambers,
                        "subjects": subjects,
                        "experiments": experiments,
                        "protocol": {
                            "name": root.protocolName,
                            "params": {}
                        }
                    }))
                }
                root.close()
            }

            /* function checkDataExists() { */
            /*     for (var idx = 0; idx < chamber_list_view.count; ++idx) { */
            /*         let item = chamber_list_view.contentItem.children[idx]; */
            /*         if (app.checkDataExists(root.dataRoot, item.cmbr, item.sbj)) */
            /*             return true; */
            /*     } */
            /*     return false; */
            /* } */

            function getChambers() {
                var chambers = []
                var subjects = []
                var experiments = []

                for (var idx = 0; idx < chamber_list_view.count; ++idx) {
                    var sbj = chamber_list_view.subjects[idx];

                    if ((typeof sbj !== 'undefined') && (sbj !== "")) {
                        var cmbr = chamber_list_view.chambers[idx];

                        if ((typeof cmbr === 'undefined') || (cmbr === ""))
                            continue;

                        var exp = chamber_list_view.experiments[idx];
                        if (typeof exp === 'undefined') exp = "";

                        chambers.push(cmbr);
                        subjects.push(sbj);
                        experiments.push(exp);
                    }
                }

                return [chambers, subjects, experiments];
            }

            onClicked: {
                /* if (checkDataExists()) { */
                /*     dialog_forceoverwrite.open(); */
                /* } */
                /* else { */
                /*     createSession(); */
                /* } */
                createSession();
            }
        }
        Button {
            id: btn_cancel
            y: parent.height - height - 5
            anchors.left: btn_create.right
            anchors.leftMargin: 5
            text: "Cancel"
            Material.foreground: "white"
            Material.background: Material.Grey

            onClicked: {
                root.close()
            }
        }
    }

    /* Dialog { */
    /*     id: dialog_forceoverwrite */
    /*     anchors.centerIn: parent */
    /*     modal: true */
    /*     standardButtons: Dialog.Yes | Dialog.No */

    /*     Label { */
    /*         text: "Data file already exists. Overwrite ?" */
    /*     } */
    /*     onAccepted: { */
    /*         btn_create.createSession(); */
    /*     } */
    /* } */

    FolderDialog {
        id: folderDialog
        onAccepted: {
            root.dataRoot = folderDialog.currentFolder
        }
    }

    Settings {
        property alias lastDataFolder: folderDialog.currentFolder
        property alias lastProtocolMade: cbox_prtc.lastProtocolMade
    }
}
