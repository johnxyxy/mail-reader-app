import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    height: 96
    radius: 8
    color: selected ? '#ecf7f2' : '#ffffff'
    border.width: selected ? 2 : 1
    border.color: selected ? '#1f8f6b' : '#d9e2ef'

    property bool selected: false
    property string email: ''
    property string remark: ''
    property string lastRefreshTime: ''
    property string lastError: ''

    signal doubleClicked()
    signal editClicked()
    signal refreshTokenClicked()
    signal deleteClicked()

    component CardAction: Rectangle {
        id: cardAction
        signal clicked()

        property string text: ''
        property color bgColor: '#eef5ff'
        property color hoverColor: '#f8fbff'
        property color downColor: '#d7e7ff'
        property color borderColor: '#c7d8f2'
        property color textColor: '#1f3b63'

        Layout.preferredHeight: 28
        radius: 6
        color: cardActionMouse.pressed ? cardAction.downColor : (cardActionMouse.containsMouse ? cardAction.hoverColor : cardAction.bgColor)
        border.color: cardAction.borderColor
        border.width: 1

        Text {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            text: cardAction.text
            color: cardAction.textColor
            font.pixelSize: 11
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        MouseArea {
            id: cardActionMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: cardAction.clicked()
        }
    }

    MouseArea {
        anchors.fill: parent
        onDoubleClicked: root.doubleClicked()
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 4

            Label {
                Layout.fillWidth: true
                text: root.remark ? root.email + ' (' + root.remark + ')' : root.email
                color: '#0f1728'
                font.pixelSize: 14
                font.bold: true
                elide: Label.ElideRight
            }

            Label {
                Layout.fillWidth: true
                text: root.lastError ? root.lastError : (root.lastRefreshTime ? (qsTr('上次刷新：') + root.lastRefreshTime) : qsTr('未刷新 Token'))
                color: root.lastError ? '#b45309' : '#6d7892'
                font.pixelSize: 11
                elide: Label.ElideRight
            }

            Item {
                Layout.fillHeight: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 3

                Item {
                    Layout.fillWidth: true
                }

                CardAction {
                    Layout.preferredWidth: 62
                    text: qsTr('编辑')
                    bgColor: '#eef5ff'
                    hoverColor: '#f8fbff'
                    downColor: '#d7e7ff'
                    borderColor: '#c7d8f2'
                    textColor: '#1f3b63'
                    onClicked: root.editClicked()
                }

                CardAction {
                    Layout.preferredWidth: 62
                    text: qsTr('删除')
                    bgColor: '#fff0f0'
                    hoverColor: '#fff8f8'
                    downColor: '#ffd8d8'
                    borderColor: '#efc2c2'
                    textColor: '#8a1f1f'
                    onClicked: root.deleteClicked()
                }

                CardAction {
                    Layout.preferredWidth: 82
                    text: qsTr('刷新 Token')
                    bgColor: '#e7f7ef'
                    hoverColor: '#f4fbf7'
                    downColor: '#cdeedd'
                    borderColor: '#b9ddca'
                    textColor: '#17624b'
                    onClicked: root.refreshTokenClicked()
                }
            }
        }
    }
}
