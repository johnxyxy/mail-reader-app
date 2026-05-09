import QtQuick
import QtQuick.Controls

Dialog {
    id: root
    modal: true
    width: 448
    height: 556
    padding: 0
    anchors.centerIn: Overlay.overlay

    property var accountData: ({})
    property string errorMessage: ''

    signal saveRequested(var payload)

    function preparePayload() {
        return {
            id: root.accountData.id ? root.accountData.id : 0,
            email: emailField.text,
            password: passwordField.text,
            client_id: clientIdField.text,
            refresh_token: refreshTokenField.text,
            remark: remarkField.text
        }
    }

    background: Rectangle {
        radius: 12
        color: '#fbfdff'
        border.color: '#d9e2ef'
    }

    onOpened: {
        titleLabel.text = root.accountData && root.accountData.id ? qsTr('编辑邮箱账号') : qsTr('新增邮箱账号')
        confirmButton.text = root.accountData && root.accountData.id ? qsTr('保存修改') : qsTr('确认新增')
        emailField.text = root.accountData.email || ''
        passwordField.text = root.accountData.password || ''
        clientIdField.text = root.accountData.client_id || root.accountData.clientId || ''
        refreshTokenField.text = root.accountData.refresh_token || root.accountData.refreshToken || ''
        remarkField.text = root.accountData.remark || ''
        root.errorMessage = ''
        emailField.forceActiveFocus()
    }

    component SectionTitle: Label {
        width: parent ? parent.width : implicitWidth
        color: '#29466f'
        font.pixelSize: 13
        font.bold: true
    }

    component SectionHint: Label {
        width: parent ? parent.width : implicitWidth
        color: '#73819a'
        font.pixelSize: 11
        wrapMode: Text.WordWrap
    }

    component SectionDivider: Rectangle {
        width: parent ? parent.width : 1
        height: 1
        color: '#e5ebf3'
    }

    component FieldLabel: Label {
        width: parent ? parent.width : implicitWidth
        color: '#0f1728'
        font.pixelSize: 12
        font.bold: true
    }

    component StyledField: TextField {
        width: parent ? parent.width : implicitWidth
        height: 28
        leftPadding: 6
        rightPadding: 6
        color: '#0f1728'
        selectedTextColor: '#ffffff'
        selectionColor: '#1f8f6b'
        verticalAlignment: TextInput.AlignVCenter

        background: Rectangle {
            radius: 6
            color: '#f8fbff'
            border.width: parent.activeFocus ? 2 : 1
            border.color: parent.activeFocus ? '#1f8f6b' : '#d4deeb'
        }
    }

    component StyledArea: TextArea {
        width: parent ? parent.width : implicitWidth
        leftPadding: 6
        rightPadding: 6
        topPadding: 5
        bottomPadding: 5
        color: '#0f1728'
        selectedTextColor: '#ffffff'
        selectionColor: '#1f8f6b'
        wrapMode: TextEdit.Wrap

        background: Rectangle {
            radius: 6
            color: '#f8fbff'
            border.width: parent.activeFocus ? 2 : 1
            border.color: parent.activeFocus ? '#1f8f6b' : '#d4deeb'
        }
    }

    component DialogButton: Rectangle {
        id: dialogButton
        signal clicked()

        property string text: ''
        property color bgColor: '#f4f7fb'
        property color hoverColor: '#fbfdff'
        property color downColor: '#e5ecf5'
        property color borderColor: '#d0dbe9'
        property color textColor: '#52637f'

        width: 100
        height: 28
        radius: 6
        color: dialogButtonMouse.pressed ? dialogButton.downColor : (dialogButtonMouse.containsMouse ? dialogButton.hoverColor : dialogButton.bgColor)
        border.color: dialogButton.borderColor

        Text {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            text: dialogButton.text
            color: dialogButton.textColor
            font.pixelSize: 13
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        MouseArea {
            id: dialogButtonMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: dialogButton.clicked()
        }
    }

    component SecondaryButton: DialogButton {
        width: 100
        bgColor: '#f4f7fb'
        hoverColor: '#fbfdff'
        downColor: '#e5ecf5'
        borderColor: '#d0dbe9'
        textColor: '#52637f'
    }

    component PrimaryButton: DialogButton {
        width: 118
        bgColor: '#e7f7ef'
        hoverColor: '#f4fbf7'
        downColor: '#cdeedd'
        borderColor: '#b9ddca'
        textColor: '#17624b'
    }

    contentItem: Item {
        anchors.fill: parent

        Rectangle {
            id: headerCard
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 8
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            height: 44
            radius: 8
            color: '#eef5ff'
            border.color: '#d3e0f2'

            Column {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 2

                Label {
                    id: titleLabel
                    width: parent.width
                    color: '#0f1728'
                    font.pixelSize: 18
                    font.bold: true
                }

                Label {
                    width: parent.width
                    text: qsTr('只需要填写可编辑字段，系统字段由程序自动维护。')
                    color: '#60708b'
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            id: errorCard
            anchors.top: headerCard.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 8
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            height: visible ? 40 : 0
            visible: root.errorMessage.length > 0
            radius: 6
            color: '#fff2f2'
            border.color: '#edc3c3'

            Label {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                verticalAlignment: Text.AlignVCenter
                text: root.errorMessage
                color: '#912121'
                wrapMode: Text.WordWrap
            }
        }

        Rectangle {
            id: footerBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            anchors.bottomMargin: 16
            height: 60
            color: 'transparent'

            Rectangle {
                anchors.fill: parent
                radius: 8
                color: '#f7f9fc'
                border.color: '#dfe7f1'
            }

            Row {
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 5

                SecondaryButton {
                    text: qsTr('取消')
                    onClicked: root.close()
                }

                PrimaryButton {
                    id: confirmButton
                    onClicked: root.saveRequested(root.preparePayload())
                }
            }
        }

        Flickable {
            id: formFlick
            anchors.top: errorCard.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: footerBar.top
            anchors.topMargin: errorCard.visible ? 8 : 0
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.bottomMargin: 8
            clip: true
            contentWidth: width
            contentHeight: formColumn.height
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                width: 8
                padding: 1

                background: Rectangle {
                    implicitWidth: 8
                    radius: 4
                    color: '#e8eef7'
                }

                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: parent.pressed ? '#1f8f6b' : (parent.hovered ? '#7f9abf' : '#b7c5d9')
                }
            }

            Column {
                id: formColumn
                width: formFlick.width
                spacing: 8

                Rectangle {
                    width: parent.width
                    height: basicSection.implicitHeight + 24
                    radius: 8
                    color: '#ffffff'
                    border.color: '#dbe4f0'

                    Column {
                        id: basicSection
                        x: 16
                        y: 16
                        width: parent.width - 32
                        spacing: 9

                        SectionTitle {
                            text: qsTr('基本信息')
                        }

                        SectionHint {
                            text: qsTr('这一组主要是账号识别信息。邮箱地址必填，备注可以用来区分用途。')
                        }

                        SectionDivider { }

                        Column {
                            width: parent.width
                            spacing: 4

                            FieldLabel {
                                text: qsTr('邮箱地址')
                            }

                            StyledField {
                                id: emailField
                                placeholderText: qsTr('例：example@outlook.com')
                            }
                        }

                        Column {
                            width: parent.width
                            spacing: 4

                            FieldLabel {
                                text: qsTr('密码')
                            }

                            StyledField {
                                id: passwordField
                                placeholderText: qsTr('选填，如果暂时不用可以不填')
                                echoMode: TextInput.Password
                            }
                        }

                        Column {
                            width: parent.width
                            spacing: 4

                            FieldLabel {
                                text: qsTr('备注')
                            }

                            StyledArea {
                                id: remarkField
                                height: 72
                                placeholderText: qsTr('例：主办公账号、测试账号、用于接收验证码')
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: authSection.implicitHeight + 24
                    radius: 8
                    color: '#ffffff'
                    border.color: '#dbe4f0'

                    Column {
                        id: authSection
                        x: 16
                        y: 16
                        width: parent.width - 32
                        spacing: 9

                        SectionTitle {
                            text: qsTr('认证信息')
                        }

                        SectionHint {
                            text: qsTr('Client ID 用于标识 OAuth 应用，Refresh Token 用于后续换取访问凭证。')
                        }

                        SectionDivider { }

                        Column {
                            width: parent.width
                            spacing: 4

                            FieldLabel {
                                text: qsTr('Client ID')
                            }

                            StyledField {
                                id: clientIdField
                                placeholderText: qsTr('请输入 OAuth 应用的 Client ID')
                            }

                            Label {
                                width: parent.width
                                text: qsTr('通常是在 Azure 或 OAuth 应用管理后台获取的应用 ID。')
                                color: '#7a879f'
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: tokenBlock.implicitHeight + 20
                            radius: 8
                            color: '#f5f9ff'
                            border.color: '#d8e4f1'

                            Column {
                                id: tokenBlock
                                x: 12
                                y: 12
                                width: parent.width - 24
                                spacing: 5

                                FieldLabel {
                                    text: qsTr('Refresh Token')
                                }

                                Label {
                                    width: parent.width
                                    text: qsTr('请粘贴完整 Token，不要手动截断或改行。')
                                    color: '#7a879f'
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                }

                                StyledArea {
                                    id: refreshTokenField
                                    height: 128
                                    placeholderText: qsTr('请粘贴完整的 Refresh Token')
                                    leftPadding: 14
                                    rightPadding: 14
                                    topPadding: 12
                                    bottomPadding: 12
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: systemSection.implicitHeight + 18
                    radius: 8
                    color: '#fff9eb'
                    border.color: '#edd9a3'

                    Column {
                        id: systemSection
                        x: 12
                        y: 11
                        width: parent.width - 24
                        spacing: 4

                        SectionTitle {
                            text: qsTr('系统字段说明')
                            color: '#7b5a12'
                            font.pixelSize: 12
                        }

                        SectionHint {
                            text: qsTr('数据库里的 last_refresh_time 和 last_error 不在这里手动编辑。程序在刷新 Token 或后续读取邮件时会自动更新这两个字段。')
                            color: '#8c6a1d'
                        }
                    }
                }
            }
        }
    }
}
