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
    property string searchKeyword: ''
    property int accountCount: 0

    signal accountOpened(int index)
    signal addAccountRequested()
    signal editAccountRequested(int index)
    signal deleteAccountRequested(int accountId)
    signal refreshTokenRequested(int accountId)
    signal searchKeywordChangedByUser(string keyword)
    signal searchRequested()
    signal showAllRequested()

    component ActionButton: Rectangle {
        id: actionButton
        signal clicked()

        property string text: ''
        property color bgColor: '#eef5ff'
        property color hoverColor: '#f8fbff'
        property color downColor: '#d7e7ff'
        property color borderColor: '#c7d8f2'
        property color textColor: '#1f3b63'

        Layout.preferredHeight: 32
        implicitHeight: 32
        radius: 6
        color: actionButtonMouse.pressed ? actionButton.downColor : (actionButtonMouse.containsMouse ? actionButton.hoverColor : actionButton.bgColor)
        border.color: actionButton.borderColor
        border.width: 1

        Text {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            text: actionButton.text
            color: actionButton.textColor
            font.pixelSize: 13
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        MouseArea {
            id: actionButtonMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: actionButton.clicked()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                spacing: 2

                Label {
                    text: qsTr('账号列表')
                    color: '#0f1728'
                    font.pixelSize: 22
                    font.bold: true
                }

                Label {
                    text: qsTr('共 ') + root.accountCount + qsTr(' 个邮箱')
                    color: '#6d7892'
                    font.pixelSize: 12
                }
            }

            Item {
                Layout.fillWidth: true
            }

            ActionButton {
                Layout.preferredWidth: 88
                text: qsTr('新增')
                bgColor: '#e7f7ef'
                downColor: '#cdeedd'
                borderColor: '#b9ddca'
                textColor: '#17624b'
                onClicked: root.addAccountRequested()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            radius: 8
            color: '#ffffff'
            border.color: '#dbe4f0'

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                ActionButton {
                    Layout.preferredWidth: 70
                    text: qsTr('全部邮箱')
                    bgColor: '#f1f5fb'
                    downColor: '#e0e8f4'
                    borderColor: '#d0dbe9'
                    textColor: '#33415f'
                    onClicked: root.showAllRequested()
                }

                Item {
                    Layout.preferredWidth: 12
                }

                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    placeholderText: qsTr('搜索邮箱或备注')
                    text: root.searchKeyword
                    color: '#0f1728'
                    selectedTextColor: '#ffffff'
                    selectionColor: '#1f8f6b'
                    leftPadding: 10
                    rightPadding: 10
                    verticalAlignment: TextInput.AlignVCenter
                    onTextChanged: root.searchKeywordChangedByUser(text)
                    onAccepted: root.searchRequested()

                    background: Rectangle {
                        radius: 6
                        color: '#f7f9fd'
                        border.color: searchField.activeFocus ? '#1f8f6b' : '#d0dbe9'
                        border.width: searchField.activeFocus ? 2 : 1
                    }
                }

                ActionButton {
                    Layout.preferredWidth: 50
                    text: qsTr('搜索')
                    bgColor: '#eef5ff'
                    downColor: '#d7e7ff'
                    borderColor: '#c7d8f2'
                    textColor: '#1f3b63'
                    onClicked: root.searchRequested()
                }
            }
        }

        ListView {
            id: accountList
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6
            clip: true
            model: root.model
            currentIndex: root.selectedIndex

            delegate: AccountCard {
                width: accountList.width
                selected: index === root.selectedIndex
                email: model.email
                remark: model.remark
                lastRefreshTime: model.lastRefreshTime
                lastError: model.lastError
                onDoubleClicked: root.accountOpened(index)
                onEditClicked: root.editAccountRequested(index)
                onRefreshTokenClicked: root.refreshTokenRequested(model.accountId)
                onDeleteClicked: root.deleteAccountRequested(model.accountId)
            }

            ScrollBar.vertical: ScrollBar {
                id: accountScrollBar
                width: 8
                policy: ScrollBar.AsNeeded
                visible: size < 1.0
                padding: 1

                background: Rectangle {
                    implicitWidth: 8
                    radius: 4
                    color: '#e8eef7'
                    opacity: accountScrollBar.hovered || accountScrollBar.pressed ? 1.0 : 0.45
                }

                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: accountScrollBar.pressed ? '#1f8f6b' : (accountScrollBar.hovered ? '#7f9abf' : '#b7c5d9')
                }
            }
        }
    }
}
