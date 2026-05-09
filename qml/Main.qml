import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "pages"
import "components"
import "dialogs"

ApplicationWindow {
    id: window
    width: 1080
    height: 640
    visible: true
    title: qsTr('邮件读取器')
    color: '#0b1020'

    function openCreateDialog() {
        if (!appController) {
            return;
        }
        appController.clearOperationMessage();
        accountDialog.accountData = ({
                "id": 0,
                "email": '',
                "password": '',
                "client_id": '',
                "refresh_token": '',
                "remark": ''
            });
        accountDialog.open();
    }

    function openEditDialog(index) {
        if (!appController) {
            return;
        }
        const account = appController.getAccount(index);
        if (!account || !account.id) {
            return;
        }
        appController.clearOperationMessage();
        accountDialog.accountData = account;
        accountDialog.open();
    }

    background: Rectangle {
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: '#18243f'
            }
            GradientStop {
                position: 0.5
                color: '#0d1628'
            }
            GradientStop {
                position: 1.0
                color: '#09111e'
            }
        }
    }

    AccountDialog {
        id: accountDialog
        errorMessage: appController ? appController.operationMessage : ''
        onSaveRequested: function (payload) {
            if (appController && appController.saveAccount(payload)) {
                accountDialog.close();
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 3

        AccountPage {
            Layout.preferredWidth: 332
            Layout.fillHeight: true
            model: appController ? appController.accountModel : null
            selectedIndex: appController ? appController.selectedAccountIndex : -1
            searchKeyword: appController ? appController.searchKeyword : ''
            accountCount: appController ? appController.accountCount : 0
            onAccountOpened: function (index) {
                if (appController) {
                    appController.openAccountInbox(index);
                }
            }
            onAddAccountRequested: window.openCreateDialog()
            onEditAccountRequested: function (index) {
                window.openEditDialog(index);
            }
            onDeleteAccountRequested: function (accountId) {
                if (appController) {
                    appController.deleteAccount(accountId);
                }
            }
            onRefreshTokenRequested: function (accountId) {
                if (appController) {
                    appController.refreshAccountToken(accountId);
                }
            }
            onSearchKeywordChangedByUser: function (keyword) {
                if (appController) {
                    appController.setSearchKeyword(keyword);
                }
            }
            onSearchRequested: {
                if (appController) {
                    appController.applyAccountSearch()
                }
            }
            onShowAllRequested: {
                if (appController) {
                    appController.showAllAccounts()
                }
            }
        }

        MailPage {
            Layout.preferredWidth: 344
            Layout.fillHeight: true
            model: appController ? appController.mailModel : null
            selectedIndex: appController ? appController.selectedMailIndex : -1
            accountEmail: appController ? appController.selectedAccountEmail : ''
            loading: appController ? appController.loading : false
            currentFolder: appController ? appController.currentFolder : 'INBOX'
            onMailSelected: function (index) {
                if (appController) {
                    appController.selectMail(index);
                }
            }
            onMailDeleteRequested: function (index) {
                if (appController) {
                    appController.deleteMail(index);
                }
            }
            onRefreshRequested: {
                if (appController) {
                    appController.refreshCurrentMailbox()
                }
            }
            onFolderChangedByUser: function (folder) {
                if (appController) {
                    appController.setCurrentFolder(folder);
                }
            }
        }

        MailDetailPage {
            Layout.fillWidth: true
            Layout.fillHeight: true
            mailData: appController ? appController.selectedMail : ({})
            accountEmail: appController ? appController.selectedAccountEmail : ''
        }
    }
}
