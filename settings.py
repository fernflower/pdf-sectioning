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
        self.all_zones = []
        self.ui.buttonBox.clicked.connect(self._apply)
        self.ui.addStart_button.clicked.connect(self._add_zone_clicked)
        self.ui.addEnd_button.clicked.connect(self._add_zone_clicked)
        self.ui.addPassthrough_button.clicked.connect(self._add_zone_clicked)
        self.ui.search_button.clicked.connect(self._find_cms_course)
        self.ui.searchResults_combo.connect(self.ui.searchResults_combo,
                                            QtCore.SIGNAL("highlighted(int)"),
                                            self._on_course_browsed)
        self.ui.searchResults_combo.connect(self.ui.searchResults_combo,
                                            QtCore.SIGNAL("currentIndexChanged(int)"),
                                            self._on_course_chosen)
        self.ui.first_page_group.connect(self.ui.leftPage_radio,
                                         QtCore.SIGNAL("toggled(bool)"),
                                         self._enable_apply)
        self.ui.margins_group.connect(self.ui.one_margin,
                                      QtCore.SIGNAL("toggled(bool)"),
                                      self._enable_apply)
        self.ui.password_edit.textChanged.connect(self._enable_apply)
        self.ui.login_edit.textChanged.connect(self._enable_apply)
        self.ui.incorrectData_label.hide()
        self.ui.searchResults_combo.hide()
        self.autozone_relations = {
            self.ui.addStart_button: self.ui.startZones_edit,
            self.ui.addEnd_button: self.ui.endZones_edit,
            self.ui.addPassthrough_button: self.ui.passthroughZones_edit }

    @property
    def apply_button(self):
        return self.ui.buttonBox.button(QtGui.QDialogButtonBox.Apply)

    @property
    def login(self):
        return unicode(self.ui.login_edit.text())

    @property
    def password(self):
        return unicode(self.ui.password_edit.text())

    def _enable_apply(self):
        self.apply_button.setEnabled(True)

    # split by comma and strip
    def _get_zones(self, text):
        return [z.strip() for z in str(text).split(",") if z != ""]

    def _get_zones_text(self, zoneslist):
        return ", ".join(z for z in zoneslist) if len(zoneslist) > 1 else \
            str(zoneslist[0] if len(zoneslist) > 0 else "")

    def _on_course_browsed(self, index):
        print "browsed"
        if index == 0:
            self.chosen_course_id = None
            self.ui.cmsCourse_edit.setText(u"")
        else:
            self.chosen_course_id = self.search_result[index - 1][1]
            self.ui.cmsCourse_edit.setText(self.search_result[index - 1][0])

    def _on_course_chosen(self, index):
        # reload course only if no marks have been placed
        # index = 0 means that nothing has been chosen
        if index == 0:
            return
        if not self.controller.any_changes and self.chosen_course_id:
            print "chosen course id is %s" % self.chosen_course_id
            self.ui.cmsCourse_edit.setText(self.search_result[index - 1][0])
            self._enable_apply()
            # load starts right after course is chosen if no changes have been
            # made
            QtGui.QApplication.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.BusyCursor))
            self.controller.load_course(self.chosen_course_id)
            self.all_zones = self.controller.all_autozones
            QtGui.QApplication.restoreOverrideCursor()
            self._let_modify_zonetypes(True)
            self._set_correct_zones_text()

    # if any of the default values are not present in zoneslist, then remove
    # these values from lineedit text
    def _set_correct_zones_text(self):
        autozones = self.controller.all_autozones
        for (w, defaults) in \
                [(self.ui.startZones_edit, self.controller.start_autozones),
                 (self.ui.endZones_edit, self.controller.end_autozones),
                 (self.ui.passthroughZones_edit, self.controller.passthrough_zones)]:
            available_data = [z for z in defaults if z in autozones]
            w.setText(self._get_zones_text(available_data))

    def _find_cms_course(self):
        # clear old data
        namepart = unicode(self.ui.cmsCourse_edit.text())
        self.ui.searchResults_combo.clear()
        self.search_result = self.controller.find_course(namepart,
                                                         self.login,
                                                         self.password)
        self.ui.searchResults_combo.show()
        if self.search_result == []:
            self.ui.searchResults_combo.clear()
            self.ui.cmsCourse_edit.setText(u"")
            self.chosen_course_id = None
        else:
            # add empty field
            self.ui.searchResults_combo.addItem(u"Результаты поиска")
            self.ui.searchResults_combo.\
                addItems([n[0] for n in self.search_result])

    def exec_(self):
        self.ui.cmsCourse_edit.setText(self.controller.display_name)
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
        if self.controller.has_both_margins():
            self.ui.two_margins.setChecked(True)
        else:
            self.ui.one_margin.setChecked(True)
        self.ui.login_edit.setText(self.controller.login)
        self.ui.password_edit.setEchoMode(
            QtGui.QLineEdit.Password)
        self.ui.password_edit.setText(self.controller.password)
        # if no login\password or bad data: deactivate other settings' tab
        self.ui.bookData_tab.setEnabled(
            self.controller.is_userdata_valid(self.login, self.password))
        self.apply_button.setEnabled(False)
        self.chosen_course_id = self.controller.cms_course
        return super(Settings, self).exec_()

    def _let_modify_zonetypes(self, value):
        for elem in [self.ui.startZones_edit, self.ui.addStart_button,
                     self.ui.endZones_edit, self.ui.addEnd_button,
                     self.ui.passthroughZones_edit,
                     self.ui.addPassthrough_button]:
            elem.setEnabled(value)

    def show_settings(self, any_markup=False):
        if any_markup or self.controller.any_changes:
            self.ui.cmsCourse_edit.setEnabled(False)
            self.ui.searchResults_combo.setEnabled(False)
            self.ui.search_button.setEnabled(False)
        self._let_modify_zonetypes(self.course_loaded)
        self.all_zones = self.controller.all_autozones or []
        self.new_settings = {}
        result = self.exec_()
        return self.new_settings

    def _apply(self, button):
        # close dialog when anything but apply is pressed
        if not button == self.apply_button:
            return
        # if course chosen -> let modify auto zones
        self._let_modify_zonetypes(self.course_loaded)
        # disable apply
        self.apply_button.setEnabled(False)
        if self.controller.is_userdata_valid(self.login, self.password):
            if not self.ui.bookData_tab.isEnabled():
                self.ui.incorrectData_label.hide()
                self.ui.bookData_tab.setEnabled(True)
            # when apply pressed and userdata valid -> collect all info
            new_course = self.ui.cmsCourse_edit.text()
            new_first = ""
            if self.ui.leftPage_radio.isChecked():
                new_first = "l"
            elif self.ui.rightPage_radio.isChecked():
                new_first = "r"
            new_margins = []
            if self.ui.one_margin.isChecked():
                new_margins = [new_first]
            else:
                new_margins = ["l", "r"]
            display_name = unicode(self.ui.cmsCourse_edit.text())
            new_start = self._get_zones(str(self.ui.startZones_edit.text()))
            new_end = self._get_zones(str(self.ui.endZones_edit.text()))
            new_pass = self._get_zones(str(self.ui.passthroughZones_edit.text()))
            self.new_settings = {"first-page": new_first,
                                 "margins": new_margins,
                                 "start-autozones": new_start,
                                 "end-autozones": new_end,
                                 "passthrough-zones": new_pass,
                                 "login": self.login,
                                 "password": self.password,
                                 "display-name": display_name,
                                 "cms-course": self.chosen_course_id or "",
                                 "all-autozones": self.all_zones}
        else:
            # if apply and userdata invalid -> save just login
            self.ui.bookData_tab.setEnabled(False)
            self.new_settings = {"login": login}
            self.ui.incorrectData_label.show()

    @property
    def course_loaded(self):
        return self.chosen_course_id is not None or self.controller.any_changes

    def _add_zone_clicked(self):
        non_intersecting = {self.ui.addStart_button: self.ui.endZones_edit,
                            self.ui.addEnd_button: self.ui.startZones_edit}
        old_data = self._get_zones(
            self.autozone_relations[self.sender()].text())
        # zones that should not appear in list of choices
        except_zones = [] if self.sender() not in non_intersecting else \
                self._get_zones(non_intersecting[self.sender()].text())
        dialog = ManageZonesDialog(self.all_zones, old_data, except_zones)
        new_data = dialog.exec_()
        self.apply_button.setEnabled(self.apply_button.isEnabled() or \
                                     new_data != old_data)
        self.autozone_relations[self.sender()].setText(
            self._get_zones_text(new_data))


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
