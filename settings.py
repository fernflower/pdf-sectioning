#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from settingsdialog import Ui_Dialog


class Settings(QtGui.QDialog):
    def __init__(self, controller, parent):
        super(Settings, self).__init__()
        self.controller = controller
        self.parent = parent
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(QtCore.QString.fromUtf8(u"Настройки"))
        self.wrong_userdata_dialog = None
        self.new_settings = None
        self.ui.buttonBox.clicked.connect(self._apply)

    def exec_(self):
        # if no login\password or bad data: deactivate other settings' tab
        self.ui.bookData_tab.setEnabled(
            self.controller.is_userdata_valid())
        # get fresh settings from controller and show them
        if self.controller.cms_course:
            self.ui.cmsCourse_edit.setText(
                    self.controller.cms_course)
        self.ui.startZones_edit.setText(
            ", ".join(z for z in self.controller.start_autozones))
        self.ui.endZones_edit.setText(
            ", ".join(z for z in self.controller.end_autozones))
        self.ui.passthroughZones_edit.setText(
            ", ".join(z for z in self.controller.passthrough_zones))
        if self.controller.first_page == "l":
            self.ui.leftPage_radio.setChecked(True)
        else:
            self.ui.rightPage_radio.setChecked(True)
        if self.controller.has_right_margin():
            self.ui.rightMargin_checkbox.setChecked(True)
        if self.controller.has_left_margin():
            self.ui.leftMargin_checkbox.setChecked(True)
        self.ui.login_edit.setText(self.controller.login)
        self.ui.password_edit.setEchoMode(
            QtGui.QLineEdit.Password)
        self.ui.password_edit.setText(self.controller.password)
        super(Settings, self).exec_()

    def show_settings(self):
        result = self.exec_()
        new_course = self.ui.cmsCourse_edit.text()
        new_first = ""
        if self.ui.leftPage_radio.isChecked():
            new_first = "l"
        elif self.ui.rightPage_radio.isChecked():
            new_first = "r"
        new_margins = []
        if self.ui.leftMargin_checkbox.isChecked():
            new_margins.append("l")
        if self.ui.rightMargin_checkbox.isChecked():
            new_margins.append("r")
        new_start = [z.strip() for z in \
                     str(self.ui.startZones_edit.text()).\
                     split(",") if z != ""]
        new_end = [z.strip() for z in \
                   str(self.ui.endZones_edit.text()).\
                   split(",") if z != ""]
        new_pass = [
            z.strip() for z in \
            str(self.ui.passthroughZones_edit.text()).\
            split(",") if z != ""]
        new_login = self.ui.login_edit.text()
        new_password = self.ui.password_edit.text()
        self.new_settings = {"cms-course": new_course,
                             "first-page": new_first,
                             "margins": new_margins,
                             "start-autozones": new_start,
                             "end-autozones": new_end,
                             "passthrough-zones": new_pass,
                             "password": new_password,
                             "login": new_login}
        print self.new_settings
        return (self.controller.is_userdata_valid(new_login, new_password),
                self.new_settings)

    def _apply(self, button):
        # close dialog when anything but apply is pressed
        if not self.ui.buttonBox.buttonRole(button) == \
                QtGui.QDialogButtonBox.ApplyRole:
            return
        login = self.ui.login_edit.text()
        password = self.ui.password_edit.text()
        if self.controller.is_userdata_valid(login, password):
            self.ui.bookData_tab.setEnabled(True)
        else:
            self.ui.bookData_tab.setEnabled(False)
            self.show_wrong_userdata_dialog()

    def show_wrong_userdata_dialog(self):
        if not self.wrong_userdata_dialog:
            self.wrong_userdata_dialog = QtGui.QMessageBox(self.parent)
            self.wrong_userdata_dialog.setText(u"Некорректные пользовательские данные.")
            self.wrong_userdata_dialog.setInformativeText(u"Убедитесь в корректности логина и пароля.")
            self.wrong_userdata_dialog.setStandardButtons(QtGui.QMessageBox.Cancel)
        self.wrong_userdata_dialog.exec_()
