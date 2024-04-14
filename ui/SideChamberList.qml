import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import neurobehavior

Item {
    id: root

    signal chamberSelected(chamberData: var)
    property Neurobehavior app

    SectionChamberList {
        id: sectionChamberList
        anchors.fill: parent
        spacing: 3
        model: app ? app.chamberList : null

        onChamberSelected: function (chamberData) {
            root.chamberSelected(chamberData);
        }
    }
}
