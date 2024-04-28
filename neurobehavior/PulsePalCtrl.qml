import QtQuick
import QtQuick.Controls
import neurobehavior

Item {
    id: root

    property Session session
    property var protocols

    /* property PulsePal pulsepal: PulsePal {} */

    ComboBox {
        id: cbox_event
        anchors.top: cbox_prtc
        model: NULL

        onActivated: {
            if (index == 0)     /* 1st index is an empty string "" */
                return
            index -= 1

            var evtname = session.protocol.events[index];
            console.log(evtname);
            pulsepal.connect_event(1, session.protocol.getEvent(evtname))
        }

        Connections {
            target: session
            onProtocolChanged: {
                cbox_event.model = [""].concat(protocol.events)
            }
        }
    }
}
