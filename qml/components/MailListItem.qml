import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    height: 72
    clip: true

    property bool selected: false
    property string subject: ''
    property string fromName: ''
    property string fromAddress: ''
    property string dateText: ''
    property bool isRead: true
    property bool deleteEnabled: true
    property bool confirmDelete: false

    readonly property real cardRadius: 8
    // 单按钮宽度要和桌面列表密度匹配；确认态会扩展成“确定 + 取消”两段。
    readonly property real actionButtonWidth: 76
    readonly property real actionWidth: confirmDelete ? actionButtonWidth * 2 : actionButtonWidth

    signal clicked()
    signal deleteConfirmed()
    signal deleteCancelled()

    // 收起滑动状态，并回到普通邮件卡片。
    function closeSwipe() {
        confirmDelete = false
        cardLayer.x = 0
    }

    // 第一段左滑只露出“删除”，不直接执行删除，避免误触。
    function revealDelete() {
        confirmDelete = false
        cardLayer.x = -actionButtonWidth
    }

    // 点击“删除”后进入确认态，再由用户点“确定”真正删除。
    function revealConfirm() {
        confirmDelete = true
        cardLayer.x = -actionWidth
    }

    Item {
        id: actionLayer
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: root.actionWidth

        // 动作层固定在右侧，白色卡片向左移动后露出它。
        Rectangle {
            visible: !root.confirmDelete
            anchors.fill: parent
            radius: root.cardRadius
            color: '#c53030'

            Text {
                anchors.centerIn: parent
                text: qsTr('删除')
                color: '#ffffff'
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                enabled: root.deleteEnabled
                onClicked: root.revealConfirm()
            }
        }

        Item {
            visible: root.confirmDelete
            anchors.fill: parent

            // 两段按钮的外侧保留圆角，内侧用补丁矩形补平，避免中间出现圆角缺口。
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: root.actionButtonWidth
                radius: root.cardRadius
                color: '#c53030'
            }

            Rectangle {
                x: root.actionButtonWidth - root.cardRadius
                width: root.cardRadius
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: '#c53030'
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                x: (root.actionButtonWidth / 2) - width / 2
                text: qsTr('确定')
                color: '#ffffff'
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                x: 0
                width: root.actionButtonWidth
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                enabled: root.deleteEnabled
                onClicked: root.deleteConfirmed()
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: root.actionButtonWidth
                radius: root.cardRadius
                color: '#6b7280'
            }

            Rectangle {
                x: root.actionButtonWidth
                width: root.cardRadius
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: '#6b7280'
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                x: root.actionButtonWidth + (root.actionButtonWidth / 2) - width / 2
                text: qsTr('取消')
                color: '#ffffff'
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                x: root.actionButtonWidth
                width: root.actionButtonWidth
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                enabled: root.deleteEnabled
                onClicked: {
                    root.closeSwipe()
                    root.deleteCancelled()
                }
            }
        }
    }

    Item {
        id: contentHost
        anchors.fill: parent

        Item {
            id: cardLayer
            width: parent.width
            height: parent.height

            Behavior on x {
                NumberAnimation {
                    duration: 160
                    easing.type: Easing.OutCubic
                }
            }

            Rectangle {
                anchors.fill: parent
                radius: root.cardRadius
                color: root.selected ? '#edf2fb' : '#ffffff'
                border.width: root.selected ? 2 : 1
                border.color: root.selected ? '#244173' : '#d9e2ef'
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 3

                Label {
                    text: root.subject
                    color: '#0f1728'
                    font.pixelSize: 13
                    font.bold: !root.isRead
                    elide: Label.ElideRight
                    Layout.fillWidth: true
                }

                Label {
                    text: root.fromName + ' <' + root.fromAddress + '>'
                    color: '#244173'
                    font.pixelSize: 11
                    elide: Label.ElideRight
                    Layout.fillWidth: true
                }

                Label {
                    text: root.dateText
                    color: '#6d7892'
                    font.pixelSize: 10
                }
            }

            MouseArea {
                id: gestureArea
                anchors.fill: parent
                hoverEnabled: true
                // 横向滑动由当前邮件项处理，减少被 ListView 的纵向滚动抢走。
                preventStealing: true
                acceptedButtons: Qt.LeftButton
                // 直接拖动卡片层，比手算每一帧的位置更稳定。
                drag.target: cardLayer
                drag.axis: Drag.XAxis
                drag.minimumX: -root.actionWidth
                drag.maximumX: 0
                property real pressX: 0
                property bool dragging: false

                onPressed: function (mouse) {
                    pressX = mouse.x
                    dragging = false
                    mouse.accepted = true
                }

                onPositionChanged: function (mouse) {
                    const delta = mouse.x - pressX
                    if (!dragging && Math.abs(delta) > 8) {
                        dragging = true
                    }
                    mouse.accepted = true
                }

                onReleased: function (mouse) {
                    const delta = mouse.x - pressX

                    if (!dragging) {
                        if (cardLayer.x !== 0) {
                            root.closeSwipe()
                        } else {
                            root.clicked()
                        }
                        return
                    }

                    if (root.confirmDelete) {
                        if (cardLayer.x < -(root.actionButtonWidth * 1.35)) {
                            root.revealConfirm()
                        } else {
                            root.closeSwipe()
                        }
                        return
                    }

                    if (delta < -30 || cardLayer.x < -(root.actionButtonWidth * 0.42)) {
                        root.revealDelete()
                    } else {
                        root.closeSwipe()
                    }
                }

                onCanceled: root.closeSwipe()
            }
        }
    }
}
