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
        self.new_settings = {}
        self.search_result = []
        self.chosen_course_id = None
        self.ui.buttonBox.clicked.connect(self._apply)
        self.ui.addStart_button.clicked.connect(self._add_zone_clicked)
        self.ui.addEnd_button.clicked.connect(self._add_zone_clicked)
        self.ui.addPassthrough_button.clicked.connect(self._add_zone_clicked)
        self.ui.search_button.clicked.connect(self._find_cms_course)
        self.ui.searchResults_combo.connect(self.ui.searchResults_combo,
                                            QtCore.SIGNAL("currentIndexChanged(int)"),
                                            self._on_course_chosen)
        self.ui.first_page_group.connect(self.ui.leftPage_radio,
                                         QtCore.SIGNAL("toggled(bool)"),
                                         self._enable_apply)
        self.ui.margins_group.connect(self.ui.leftMargin_checkbox,
                                      QtCore.SIGNAL("toggled(bool)"),
                                      self._enable_apply)
        self.ui.margins_group.connect(self.ui.rightMargin_checkbox,
                                      QtCore.SIGNAL("toggled(bool)"),
                                      self._enable_apply)
        self.ui.searchResults_combo.hide()
        self.autozone_relations = {
            self.ui.addStart_button: self.ui.startZones_edit,
            self.ui.addEnd_button: self.ui.endZones_edit,
            self.ui.addPassthrough_button: self.ui.passthroughZones_edit }

    @property
    def apply_button(self):
        return self.ui.buttonBox.button(QtGui.QDialogButtonBox.Apply)

    def _enable_apply(self):
        self.apply_button.setEnabled(True)

    # split by comma and strip
    def _get_zones(self, text):
        return [z.strip() for z in str(text).split(",") if z != ""]

    def _get_zones_text(self, zoneslist):
        return ", ".join(z for z in zoneslist) if len(zoneslist) > 1 else \
            str(zoneslist[0] if len(zoneslist) > 0 else "")

    def _on_course_chosen(self, index):
        self.chosen_course_id = self.search_result[index][1]
        self.ui.cmsCourse_edit.setText(self.search_result[index][0])
        self._enable_apply()

    def _find_cms_course(self):
        # clear old data
        namepart = unicode(self.ui.cmsCourse_edit.text())
        self.ui.searchResults_combo.clear()
        self.search_result = self.controller.find_course(namepart)
        self.ui.searchResults_combo.show()
        if self.search_result == []:
            self.ui.searchResults_combo.clear()
            self.ui.cmsCourse_edit.setText(u"")
            self.chosen_course_id = None
        else:
            self.ui.searchResults_combo.\
                addItems([n[0] for n in self.search_result])

    def exec_(self):
        self.chosen_course_id = None
        self.ui.cmsCourse_edit.setText(self.controller.display_name)
        # if no login\password or bad data: deactivate other settings' tab
        self.ui.bookData_tab.setEnabled(
            self.controller.is_userdata_valid())
        # get fresh settings from controller and show them
        if self.controller.cms_course:
            self.ui.cmsCourse_edit.setText(self.controller.display_name)
            self.ui.searchResults_combo.hide()
        self.ui.startZones_edit.setText(
            self._get_zones_text(self.controller.start_autozones))
        self.ui.endZones_edit.setText(
            self._get_zones_text(self.controller.end_autozones))
        self.ui.passthroughZones_edit.setText(
            self._get_zones_text(self.controller.passthrough_zones))
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
        self.apply_button.setEnabled(False)
        return super(Settings, self).exec_()

    def _let_modify_zonetypes(self, value):
        for elem in [self.ui.startZones_edit, self.ui.addStart_button,
                     self.ui.endZones_edit, self.ui.addEnd_button,
                     self.ui.passthroughZones_edit,
                     self.ui.addPassthrough_button]:
            elem.setEnabled(value)

    def show_settings(self, any_markup=False):
        if any_markup:
            self.ui.cmsCourse_edit.setEnabled(False)
            self.ui.searchResults_combo.setEnabled(False)
            self.ui.search_button.setEnabled(False)
        result = self.exec_()
        return self.new_settings

    def _apply(self, button):
        # close dialog when anything but apply is pressed
        if not button == self.apply_button:
            return
        # disable apply
        self.apply_button.setEnabled(False)
        login = str(self.ui.login_edit.text())
        password = str(self.ui.password_edit.text())
        if self.controller.is_userdata_valid(login, password):
            # when apply pressed and userdata valid -> collect all info
            self.ui.bookData_tab.setEnabled(True)
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
            display_name = unicode(self.ui.cmsCourse_edit.text())
            new_start = self._get_zones(str(self.ui.startZones_edit.text()))
            new_end = self._get_zones(str(self.ui.endZones_edit.text()))
            new_pass = self._get_zones(str(self.ui.passthroughZones_edit.text()))
            self.new_settings = {"first-page": new_first,
                                 "margins": new_margins,
                                 "start-autozones": new_start,
                                 "end-autozones": new_end,
                                 "passthrough-zones": new_pass,
                                 "password": password,
                                 "login": login,
                                 "display-name": display_name,
                                 "cms-course": self.chosen_course_id or ""}
        else:
            # if apply and userdata invalid -> save just login
            self.ui.bookData_tab.setEnabled(False)
            self.new_settings = {"login": login}
            self.show_wrong_userdata_dialog()

    @property
    def markup_loaded(self):
        return not self.ui.cmsCourse_edit.isEnabled()

    def _add_zone_clicked(self):
        old_data = self._get_zones(
            self.autozone_relations[self.sender()].text())
        except_zones = []
        if self.sender() == self.ui.addEnd_button:
            except_zones = self._get_zones(self.ui.startZones_edit.text())
        all_zones = self.controller.autozone_types \
            if self.markup_loaded else ZONE_TYPES
        dialog = ManageZonesDialog(all_zones, old_data, except_zones)
        new_data = dialog.exec_()
        self.apply_button.setEnabled(self.apply_button.isEnabled() or \
                                     new_data != old_data)
        self.autozone_relations[self.sender()].setText(
            self._get_zones_text(new_data))
        if self.sender() == self.ui.addStart_button:
            new_end = [z for z in except_zones if z not in new_data]
            self.ui.endZones_edit.setText(self._get_zones_text(new_end))

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

    def __init__(self, all_zones, chosen_zones, except_zones=[]):
        super(ManageZonesDialog, self).__init__()
        self.ui = Ui_addZones()
        self.ui.setupUi(self)
        self.views = {self.ALL_ZONES_MODE: self.ui.allZones_listview,
                      self.CHOSEN_ZONES_MODE: self.ui.chosenZones_listview}
        def _fill_view(view, data):
            model = QtGui.QStandardItemModel()
            for item in data:
                model.appendRow(QtGui.QStandardItem(item))
            view.setModel(model)
            # connect update func as well
            view.connect(
                view.selectionModel(),
                QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                self.update)
        all_zones_data = [zt for zt in all_zones if zt not in chosen_zones \
                            and zt not in except_zones]
        _fill_view(self.ui.allZones_listview, all_zones_data)
        _fill_view(self.ui.chosenZones_listview, chosen_zones)
        # select first elem if any
        if len(all_zones_data) > 0:
            self.ui.allZones_listview.setCurrentIndex(
                self.ui.allZones_listview.model().item(0).index())
        self.ui.add_button.clicked.connect(self.add_zone)
        self.ui.remove_button.clicked.connect(self.remove_zone)
        self.ui.up_button.clicked.connect(self.move_up)
        self.ui.down_button.clicked.connect(self.move_down)

    def exec_(self):
        super(ManageZonesDialog, self).exec_()
        return self.get_zones(self.CHOSEN_ZONES_MODE)

    def get_zones(self, mode):
        model = self.views[mode].model()
        return [str(model.item(i).text()) for i in range(0, model.rowCount())]

    def add_zone(self):
        return self._add_zone(self.CHOSEN_ZONES_MODE, self.ALL_ZONES_MODE)

    def remove_zone(self):
        return self._add_zone(self.ALL_ZONES_MODE, self.CHOSEN_ZONES_MODE)

    def move_up(self):
        self._move(-1)

    def move_down(self):
        self._move(1)

    def _get_selected(self, mode):
        idx = self.views[mode].selectedIndexes()
        if len(idx) > 0:
            return self.views[mode].model().itemFromIndex(idx[0])
        return None

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
                (row_num == view.model().rowCount() - 1 and delta > 0):
            view.selectionModel().select(selected.index(),
                                         view.selectionModel().Select)
            return
        new_row_num = row_num + delta
        row_items = view.model().takeRow(row_num)
        view.model().insertRow(new_row_num, row_items)
        view.selectionModel().select(view.model().item(new_row_num).index(),
                                     view.selectionModel().Select)

    def update(self):
        # clear selection in other view
        for button in [self.ui.up_button, self.ui.down_button,
                       self.ui.remove_button]:
            button.setEnabled(
                self._get_selected(self.CHOSEN_ZONES_MODE) is not None)
        self.ui.add_button.setEnabled(
            self._get_selected(self.ALL_ZONES_MODE) is not None)
        for viewmode in self.views:
            if not self.views[viewmode].hasFocus() and \
                    self.views[viewmode].selectionModel() != self.sender():
                self.views[viewmode].clearSelection()
        super(ManageZonesDialog, self).update()
