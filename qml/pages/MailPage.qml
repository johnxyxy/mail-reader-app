import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import '../components'

Rectangle {
    id: root
    color: '#f4f7fb'
    radius: 12
    border.color: '#d9e2ef'

    property var model
    property int selectedIndex: -1
    property string accountEmail: ''
    property bool loading: false
    property string currentFolder: 'INBOX'

    signal mailSelected(int index)
    signal mailDeleteRequested(int index)
    signal refreshRequested()
    signal folderChangedByUser(string folder)

    component ActionButton: Rectangle {
        id: actionButton
        signal clicked()

        property string text: ''
        property color bgColor: '#eef5ff'
        property color hoverColor: '#f8fbff'
        property color downColor: '#d7e7ff'
        property color borderColor: '#c7d8f2'
        property color textColor: '#1f3b63'

        Layout.minimumWidth: implicitWidth
        Layout.preferredHeight: 32
        implicitWidth: actionText.implicitWidth + 24
        implicitHeight: 32
        radius: 6
        opacity: enabled ? 1.0 : 0.55
        color: actionButtonMouse.pressed ? actionButton.downColor : (actionButtonMouse.containsMouse ? actionButton.hoverColor : actionButton.bgColor)
        border.color: actionButton.borderColor
        border.width: 1

        Text {
            id: actionText
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            text: actionButton.text
            color: actionButton.textColor
            font.pixelSize: 12
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        MouseArea {
            id: actionButtonMouse
            anchors.fill: parent
            enabled: actionButton.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: actionButton.clicked()
        }
    }

    component FolderButton: Rectangle {
        id: folderButton
        signal clicked()

        property string text: ''
        property string folderValue: 'INBOX'
        property bool checked: root.currentFolder === folderValue

        Layout.minimumWidth: implicitWidth
        Layout.preferredHeight: 32
        implicitWidth: folderText.implicitWidth + 24
        implicitHeight: 32
        radius: 6
        opacity: enabled ? 1.0 : 0.55
        color: folderButton.checked ? '#e7f7ef' : (folderButtonMouse.containsMouse ? '#fbfdff' : '#f4f7fb')
        border.color: folderButton.checked ? '#b9ddca' : '#d0dbe9'
        border.width: 1

        Text {
            id: folderText
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            text: folderButton.text
            color: folderButton.checked ? '#17624b' : '#43536f'
            font.pixelSize: 12
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        MouseArea {
            id: folderButtonMouse
            anchors.fill: parent
            enabled: folderButton.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                folderButton.clicked()
                root.folderChangedByUser(folderButton.folderValue)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                spacing: 2

                Label {
                    text: qsTr('邮件列表')
                    color: '#0f1728'
                    font.pixelSize: 22
                    font.bold: true
                }

                Label {
                    text: root.loading ? qsTr('正在读取邮件...') : (root.accountEmail ? root.accountEmail : qsTr('请先选择左侧账号'))
                    color: '#6d7892'
                    font.pixelSize: 12
                    elide: Label.ElideRight
                    Layout.preferredWidth: 120
                }
            }

            Item {
                Layout.fillWidth: true
            }

            ActionButton {
                Layout.preferredWidth: 74
                text: qsTr('刷新邮件')
                bgColor: '#e7f7ef'
                downColor: '#cdeedd'
                borderColor: '#b9ddca'
                textColor: '#17624b'
                enabled: !root.loading
                onClicked: root.refreshRequested()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            Layout.minimumHeight: 34
            spacing: 6

            FolderButton {
                text: qsTr('收件箱')
                Layout.preferredWidth: 72
                folderValue: 'INBOX'
                enabled: !root.loading
            }

            FolderButton {
                text: qsTr('垃圾箱')
                Layout.preferredWidth: 72
                folderValue: 'Junk'
                enabled: !root.loading
            }

            Item { Layout.fillWidth: true }
        }

        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.model
            currentIndex: root.selectedIndex

            delegate: MailListItem {
                width: listView.width
                selected: index === root.selectedIndex
                subject: model.subject
                fromName: model.fromName
                fromAddress: model.fromAddress
                dateText: model.dateText
                isRead: model.isRead
                deleteEnabled: !root.loading
                onClicked: root.mailSelected(index)
                onDeleteConfirmed: root.mailDeleteRequested(index)
            }

            ScrollBar.vertical: ScrollBar {
                id: mailScrollBar
                width: 8
                policy: ScrollBar.AsNeeded
                visible: size < 1.0
                padding: 1

                background: Rectangle {
                    implicitWidth: 8
                    radius: 4
                    color: '#e8eef7'
                    opacity: mailScrollBar.hovered || mailScrollBar.pressed ? 1.0 : 0.45
                }

                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: mailScrollBar.pressed ? '#1f8f6b' : (mailScrollBar.hovered ? '#7f9abf' : '#b7c5d9')
                }
            }
        }
    }
}
