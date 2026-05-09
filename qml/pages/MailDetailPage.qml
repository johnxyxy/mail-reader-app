import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: '#f4f7fb'
    radius: 12
    border.color: '#d9e2ef'

    property var mailData: ({})
    property string accountEmail: ''
    readonly property string displaySubject: root.mailData.subject ? root.mailData.subject : qsTr('邮件正文')
    readonly property string displayAccount: root.accountEmail ? ('当前邮箱：' + root.accountEmail) : qsTr('请先选择一个邮箱')
    readonly property string displayFrom: root.mailData.from_name ? ('发件人：' + root.mailData.from_name + ' <' + root.mailData.from_address + '>') : qsTr('发件人：-')
    readonly property string displayTo: root.mailData.to_address ? ('收件人：' + root.mailData.to_address) : qsTr('收件人：-')
    readonly property string displayDate: root.mailData.date_text ? ('时间：' + root.mailData.date_text) : qsTr('时间：-')
    readonly property string plainBodyText: root.mailData.body_text ? root.mailData.body_text : qsTr('请选择中间列表中的邮件查看正文。')
    readonly property bool hasHtmlBody: !!(root.mailData.body_html && String(root.mailData.body_html).trim().length > 0)
    readonly property string htmlBody: root.hasHtmlBody ? root.wrapHtmlDocument(root.mailData.body_html) : root.wrapPlainText(root.plainBodyText)

    function wrapPlainText(text) {
        const safeText = String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
        return "<html><body style='margin:0; font-family:\"Microsoft YaHei UI\"; font-size:14px; line-height:1.8; color:#21314d; white-space:pre-wrap;'>" + safeText + "</body></html>"
    }

    function wrapHtmlDocument(html) {
        return "<html><head><style>" +
            "body { font-family: \"Microsoft YaHei UI\"; font-size: 14px; line-height: 1.8; color: #21314d; margin: 0; word-wrap: break-word; }" +
            "p, div, td, li, span { line-height: 1.8; }" +
            "img { max-width: 100%; height: auto; display: inline-block; }" +
            "a { color: #1f5ea8; text-decoration: none; }" +
            "a:hover { text-decoration: underline; }" +
            "blockquote { margin: 12px 0; padding: 10px 14px; border-left: 3px solid #c8d7ea; background: #f7fafd; color: #51637f; }" +
            "pre { white-space: pre-wrap; word-break: break-word; background: #f4f7fb; padding: 10px 12px; border-radius: 6px; }" +
            "code { font-family: Consolas, \"Courier New\", monospace; }" +
            "table { border-collapse: collapse; max-width: 100%; }" +
            "td, th { vertical-align: top; }" +
            "</style></head><body>" + html + "</body></html>"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 4

        Label {
            text: root.displaySubject
            color: '#0f1728'
            font.pixelSize: 22
            font.bold: true
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: infoLayout.implicitHeight + 20
            radius: 8
            color: '#ffffff'
            border.color: '#dbe4f0'

            ColumnLayout {
                id: infoLayout
                anchors.fill: parent
                anchors.margins: 10
                spacing: 6

                Label {
                    text: root.displayAccount
                    color: '#6d7892'
                    font.pixelSize: 12
                    elide: Label.ElideRight
                    Layout.fillWidth: true
                }

                Label {
                    text: root.displayFrom
                    color: '#0f1728'
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Label {
                    text: root.displayTo
                    color: '#0f1728'
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Label {
                    text: root.displayDate
                    color: '#6d7892'
                    font.pixelSize: 12
                    Layout.fillWidth: true
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 8
            color: '#ffffff'
            border.color: '#dbe4f0'

            ScrollView {
                id: bodyScrollView
                anchors.fill: parent
                anchors.margins: 10
                clip: true

                ScrollBar.vertical: ScrollBar {
                    id: detailScrollBar
                    width: 8
                    policy: ScrollBar.AsNeeded
                    visible: size < 1.0
                    padding: 1

                    background: Rectangle {
                        implicitWidth: 8
                        radius: 4
                        color: '#e8eef7'
                        opacity: detailScrollBar.hovered || detailScrollBar.pressed ? 1.0 : 0.45
                    }

                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: 3
                        color: detailScrollBar.pressed ? '#1f8f6b' : (detailScrollBar.hovered ? '#7f9abf' : '#b7c5d9')
                    }
                }

                TextEdit {
                    width: bodyScrollView.availableWidth
                    text: root.htmlBody
                    textFormat: TextEdit.RichText
                    wrapMode: TextEdit.Wrap
                    readOnly: true
                    selectByMouse: true
                    color: '#21314d'
                    font.pixelSize: 14
                }
            }
        }
    }
}