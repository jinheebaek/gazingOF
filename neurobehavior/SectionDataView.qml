import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import neurobehavior

Item {
    id: root

    property Neurobehavior app
    property Session session
    property Chamber chamber

    property var compTabbutton
    property var compTableView
    property var tabbuttons: ({})
    property var tables: ({})

    property string currTblName

    Connections {
        target: app
        function onDataUpdated(cmbrName, tblName, tblData) {
            if (!root.chamber || !root.session)
                return;

            if ((root.chamber.name != cmbrName) ||
                (root.session.name != root.chamber.session.name))
                return;

            if (!(tblName in root.tables))
                createTbl(tblName);

            resetTbl(tblName, tblData);
        }
        function onDataAppended(cmbrName, tblName, rowData) {
            if (!root.chamber || !root.session)
                return;

            if ((root.chamber.name != cmbrName) ||
                (root.session.name != root.chamber.session.name))
                return;

            if (!(tblName in root.tables))
                createTbl(tblName);

            addRow(tblName, rowData);
        }
    }

    Connections {
        target: session
        function onSessionStarted() {
            root.reset();
        }
    }

    Component.onCompleted: {
        root.compTabbutton = Qt.createComponent("ComponentDataTabbutton.qml");
        root.compTableView = Qt.createComponent("ComponentDataTableView.qml");
    }

    onChamberChanged: {
        root.reset();
    }

    onSessionChanged: {
        root.reset();
    }

    function reset() {
        root.clearTbl();

        if (!app)
            return;

        var dataset = app.getData(root.session, root.chamber);
        dataset = JSON.parse(dataset);
        var tblnames = Object.keys(dataset);
        for (var i = 0; i < tblnames.length; i++) {
            let name = tblnames[i];
            let data = dataset[name];
            data = JSON.stringify(data)
            root.createTbl(name);
            root.resetTbl(name, data);
        }
    }

    function createTbl(tblName) {
        var added_btn = compTabbutton.createObject(
            tabbar_row,
            {"tbar": tabbar, "name": tblName,
             "index": Object.keys(root.tabbuttons).length}
        );
        root.tabbuttons[tblName] = added_btn;

        var added_tbl = compTableView.createObject(
            stack_tables,
            {}
            /* {"anchors.fill": stack_tables} */
        );
        root.tables[tblName] = added_tbl;
    }

    function resetTbl(tblName, tblData) {
        root.tables[tblName].table.setData(tblData);
    }

    function addRow(tblName, rowData) {
        root.tables[tblName].table.addRow(rowData);
    }

    function clearTbl() {
        var tblnames = Object.keys(root.tabbuttons)
        for (var i = 0; i < tblnames.length; i++) {
            let key = tblnames[i];
            root.tabbuttons[key].destroy();
            root.tables[key].destroy();
        }
        root.tabbuttons = {};
        root.tables = {};
        tabbar.currentIndex = 0;
    }

    Item {
        id: sectionTitle
        width: parent.width
        height: txtTitle.height + 10
        Text {
            id: txtTitle
            x: 15
            width: parent.width - 30

            text: "Session Data"
            color: "white"
            font.pointSize: 18
        }
    }

    Item {
        id: tabbar
        anchors.top: sectionTitle.bottom
        x: 25
        width: parent.width - 50
        height: 30
        property int currentIndex: 0

        onCurrentIndexChanged: function() {
            var tblnames = Object.keys(root.tabbuttons)
            for (var i = 0; i < tblnames.length; i++) {
                let key = tblnames[i];
                if (root.tabbuttons[key].index == currentIndex) {
                    root.currTblName = key;
                }
            }
        }

        Row {
            id: tabbar_row
        }
    }

    StackLayout {
        id: stack_tables
        x: 25
        anchors.top: tabbar.bottom
        anchors.topMargin: 5
        width: parent.width - 50
        height: parent.height - tabbar.height - sectionTitle.height - 5
        currentIndex: tabbar.currentIndex
   }
}
