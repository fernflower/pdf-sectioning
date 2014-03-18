#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from settingsdialog import Ui_Dialog
from addzonesdialog import Ui_addZones
from zonetypes import ZONE_TYPES


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
        self.ui.addStart_button.clicked.connect(self._add_zone_clicked)
        self.ui.addEnd_button.clicked.connect(self._add_zone_clicked)
        self.ui.addPassthrough_button.clicked.connect(self._add_zone_clicked)
        self.autozone_relations = {
            self.ui.addStart_button: self.controller.start_autozones,
            self.ui.addEnd_button: self.controller.end_autozones,
            self.ui.addPassthrough_button: self.controller.passthrough_zones }

    # split by comma and strip
    def _get_zones(self, text):
        return [z.strip() for z in text.split(",") if z != ""]

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
        new_margins = ""
        if self.ui.leftMargin_checkbox.isChecked():
            new_margins = new_margins + "l"
        if self.ui.rightMargin_checkbox.isChecked():
            new_margins = new_margins + "r"
        new_start = self._get_zones(str(self.ui.startZones_edit.text()))
        new_end = self._get_zones(str(self.ui.endZones_edit.text()))
        new_pass = self._get_zones(str(self.ui.passthroughZones_edit.text()))
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

    def _add_zone_clicked(self):
        dialog = ManageZonesDialog(self.autozone_relations[self.sender()])
        dialog.exec_()

    def show_wrong_userdata_dialog(self):
        if not self.wrong_userdata_dialog:
            self.wrong_userdata_dialog = QtGui.QMessageBox(self.parent)
            self.wrong_userdata_dialog.setText(u"Некорректные пользовательские данные.")
            self.wrong_userdata_dialog.setInformativeText(u"Убедитесь в корректности логина и пароля.")
            self.wrong_userdata_dialog.setStandardButtons(QtGui.QMessageBox.Cancel)
        self.wrong_userdata_dialog.exec_()


class ManageZonesDialog(QtGui.QDialog):
    ALL_ZONES_MODE = "all"
    CHOSEN_ZONES_MODE = "chosen"

    def __init__(self, chosen_zones):
        super(ManageZonesDialog, self).__init__()
        self.ui = Ui_addZones()
        self.ui.setupUi(self)
        def _fill_view(view, data):
            model = QtGui.QStandardItemModel()
            for item in data:
                model.appendRow(QtGui.QStandardItem(item))
            view.setModel(model)
        _fill_view(self.ui.allZones_listview, ZONE_TYPES)
        _fill_view(self.ui.chosenZones_listview, chosen_zones)
        self.ui.add_button.clicked.connect(self.add_zone)
        self.ui.remove_button.clicked.connect(self.remove_zone)
        self.ui.up_button.clicked.connect(self.move_up)
        self.ui.down_button.clicked.connect(self.move_down)
        self.views = {self.ALL_ZONES_MODE: self.ui.allZones_listview,
                      self.CHOSEN_ZONES_MODE: self.ui.chosenZones_listview}

    def get_zones(self, mode):
        model = self.views[mode].model()
        return [str(model.item(i).text()) for i in range(0, model.rowCount())]

    def _add_zone(self, add_to_mode, remove_from_mode):
        selected = self._get_selected(remove_from_mode)
        model_add = self.views[add_to_mode].model()
        model_remove = self.views[remove_from_mode].model()
        if not selected:
            return
        # add to new list
        if str(selected.text()) not in self.get_zones(add_to_mode):
            model_add.appendRow(QtGui.QStandardItem(selected.text()))
        # remove from old list
        if str(selected.text()) in self.get_zones(remove_from_mode):
            model_remove.removeRow(
                self.get_zones(remove_from_mode).index(str(selected.text())))

    def _move(self, delta):
        selected = self._get_selected(self.CHOSEN_ZONES_MODE)
        view = self.views[self.CHOSEN_ZONES_MODE]
        if not selected:
            return
        view.selectionModel().clear()
        row_num = self.get_zones(self.CHOSEN_ZONES_MODE).\
            index(str(selected.text()))
        if (row_num == 0 and delta < 0) or \
                (row_num == view.model().rowCount() and delta > 0):
            return
        new_row_num = row_num + delta
        row_items = view.model().takeRow(row_num)
        view.model().insertRow(new_row_num, row_items)
        view.selectionModel().select(view.model().item(new_row_num).index(),
                                     view.selectionModel().Select)

    def add_zone(self):
        return self._add_zone(self.CHOSEN_ZONES_MODE, self.ALL_ZONES_MODE)

    def remove_zone(self):
        return self._add_zone(self.ALL_ZONES_MODE, self.CHOSEN_ZONES_MODE)

    def move_up(self):
        self._move(-1)

    def move_down(self):
        print "down"
        self._move(1)

    def _get_selected(self, mode):
        idx = self.views[mode].selectedIndexes()
        if len(idx) > 0:
            return self.views[mode].model().itemFromIndex(idx[0])
        return None

    def update(self):
        selected = self._get_selected(CHOSEN_ZONES_MODE)
        print selected
        self.ui.up_button.setEnabled(selected is not None)
        self.ui.down_button.setEnabled(selected is not None)
        super(ManageZonesDialog, self).update()
