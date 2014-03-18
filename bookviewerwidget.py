#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from toolbarpart import Ui_ToolBarPart
from imagelabel import QImageLabel
from console import QConsole
from stylesheets import GENERAL_STYLESHEET, BLACK_LABEL_STYLESHEET
from selectionviewcontroller import SelectionViewController
from settings import Settings


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    TOTAL_PAGES_TEXT = u"%d из %d"
    # TODO modes must match those in bookcontroller!
    SECTION_MODE = "section_mode"
    MARKUP_MODE = "markup_mode"
    TAB_MODE = { 0: SECTION_MODE,
                 1: MARKUP_MODE }

    def __init__(self, controller, toc_controller):
        super(BookViewerWidget, self).__init__()
        self.setupUi(self)
        self.controller = controller
        self.last_right_click = None
        self.last_zoom_index = 0
        self.last_open_doc_name = None
        self.pageNum = 1
        # after widgets initiation pass view's name to toccontroller
        self.toc_controller = toc_controller
        self.toc_controller.set_views(self.listView, self.treeView)
        self.toc_controller.set_pagenum_func(self.pagenum_func)
        # mark to navigate (useful in errors navigation)
        self.mark_to_navigate = None
        # in order to implement navigation on toc-elem click. Store last mark
        # navigated to here
        # dialogs
        self.unsaved_changes_dialog = None
        self.cant_save_dialog = None
        self.cant_open_dialog = None
        self.save_as_dialog = None
        self.file_exists_dialog = None
        self.wipe_all_dialog = None
        self.settings_dialog = None
        self.init_actions()
        self.init_widgets()
        self.init_menubar()
        if self.controller.is_file_given():
            self._set_widgets_data_on_doc_load()

    # properties of most typically used child widgets in order to write less
    # code
    @property
    def totalPagesLabel(self):
        return self.toolbarpart.totalPages_label

    @property
    def spinBox(self):
        return self.toolbarpart.pagesSpinBox

    @property
    def nextPage_button(self):
        return self.toolbarpart.nextPage_button

    @property
    def prevPage_button(self):
        return self.toolbarpart.prevPage_button

    @property
    def zoom_comboBox(self):
        return self.toolbarpart.zoomComboBox

    def pagenum_func(self):
        return self.pageNum

    def generate_toolbutton_stylesheet(self, button_name):
        return  \
            """
            QToolButton {
                        border: none;
                        background: url(%s.png) top center no-repeat;
            }
            QToolButton:hover {
                background: url(%s_hover.png) top center no-repeat;
            }
            QToolButton:pressed, QToolButton:checked {
                        background: url(%s_pressed.png) top center no-repeat;
                        color: gray;}
            QToolButton:disabled {
                        background: url(%s_disabled.png) top center no-repeat;
            }
        """ % (button_name, button_name, button_name, button_name)

    def generate_menubutton_stylesheet(self, action, icon_file):
        button = self.toolBar.widgetForAction(action)
        button.setStyleSheet("""
                             QToolButton:hover { border: none;
                                                 color: gray } """)
        icon_on = QtGui.QIcon()
        icon_on.addPixmap(QtGui.QPixmap(
            QtCore.QString.fromUtf8("%s.png" % icon_file)),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On)
        icon_on.addPixmap(QtGui.QPixmap(
            QtCore.QString.fromUtf8("%s_hover.png" % icon_file)),
            QtGui.QIcon.Active,
            QtGui.QIcon.On)
        icon_on.addPixmap(QtGui.QPixmap(
            QtCore.QString.fromUtf8("%s_disabled.png" % icon_file)),
            QtGui.QIcon.Disabled,
            QtGui.QIcon.Off)
        icon_on.addPixmap(QtGui.QPixmap(
            QtCore.QString.fromUtf8("%s_pressed.png" % icon_file)),
            QtGui.QIcon.Selected,
            QtGui.QIcon.On)
        action.setIcon(icon_on)

    def init_actions(self):
        self.actionLoad_pdf.triggered.connect(self.open_file)
        self.actionLoad_pdf.setShortcut('Ctrl+O')
        self.actionLoad_markup.triggered.connect(self.load_markup)
        self.actionLoad_markup.setShortcut('Ctrl+M')
        self.actionLoad_markup.setEnabled(False)
        self.actionSave = QtGui.QAction(QtCore.QString.fromUtf8(u'Сохранить'),
                                        self)
        self.actionSave.triggered.connect(self.save)
        self.actionSave.setShortcut('Ctrl+S')
        self.actionSaveAs = QtGui.QAction(
            QtCore.QString.fromUtf8(u'Сохранить как ...'), self)
        self.actionSaveAs.triggered.connect(self.save_as)
        self.actionSaveAs.setShortcut('Ctrl+Shift+S')
        self.actionSmartSave.triggered.connect(self.smart_save)
        self.actionSetVerticalRuler.triggered.connect(
            self.set_vertical_ruler_state)
        self.actionSetVerticalRuler.setShortcut('v')
        self.actionSetHorizontalRuler.triggered.connect(
            self.set_horizontal_ruler_state)
        self.actionSetHorizontalRuler.setShortcut('h')
        self.actionPrev_page = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Предыдущая страница"), self)
        self.actionNext_page = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Следующая страница"), self)
        self.actionPrev_page.triggered.connect(self.prev_page)
        self.actionNext_page.triggered.connect(self.next_page)
        self.actionDelete_selection = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Удалить объект"), self)
        self.actionDelete_selection.setShortcut('Delete')
        self.actionDelete_selection.triggered.connect(self.delete_marks)
        self.actionForced_delete_selection = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Удалить активную зону"), self)
        self.actionForced_delete_selection.setShortcut('Shift+Delete')
        self.actionForced_delete_selection.triggered.connect(
            self.delete_marks_forced)
        self.actionDelete_all = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Удалить текущую разметку"), self)
        self.actionDelete_all.setShortcut('Ctrl+Shift+Delete')
        self.actionDelete_all.triggered.connect(self.delete_all)
        self.actionClose = QtGui.QAction(
            QtCore.QString.fromUtf8(u"Выход"), self)
        self.actionClose.triggered.connect(self.close)

    # called after all actions and widgets are created
    def init_menubar(self):
        # fill file/edit/view menus
        self.menuFile.addAction(self.actionLoad_pdf)
        self.menuFile.addAction(self.actionLoad_markup)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionClose)
        self.menuEdit.addAction(self.actionDelete_selection)
        self.menuEdit.addAction(self.actionForced_delete_selection)
        self.menuEdit.addAction(self.actionDelete_all)
        self.menuTools.addAction(self.actionSetHorizontalRuler)
        self.menuTools.addAction(self.actionSetVerticalRuler)

    def init_widgets(self):
        self.imageLabel = QImageLabel(self, self.controller,
                                      self.toc_controller)
        self.imageLabel.setScaledContents(True)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setGeometry(self.scrollArea.x(),
                                    self.scrollArea.y(),
                                    self.frameSize().width(),
                                    self.frameSize().height())
        # add spinbox to toolbar
        self.toolbarpart = Ui_ToolBarPart()
        self.toolbarpart.setupUi(self)
        self.spinBox.connect(self.spinBox,
                             QtCore.SIGNAL("valueChanged(int)"),
                             self.go_to_page)
        self.imageLabel.connect(self.imageLabel,
                                QtCore.SIGNAL("zoomChanged(float)"),
                                self.on_zoom_changed)
        self.zoom_comboBox.connect(self.zoom_comboBox,
                                   QtCore.SIGNAL("currentIndexChanged(int)"),
                                   self.on_zoom_value_change)
        self.tabWidget.connect(self.tabWidget,
                               QtCore.SIGNAL("currentChanged(int)"),
                               self.on_tab_switched)
        # add console
        self.console = QConsole(self.tab, self.verticalLayout, self)
        self.setFocus(True)
        # fill tab1 and tab2 with data
        self._fill_views()
        self.listView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.treeView.header().hide()
        # clicked, not any other event as click on already selected has it's
        # own special meaning (navigation to page with next elem)
        self.listView.clicked.connect(self.on_selected)
        self.treeView.clicked.connect(self.on_selected)
        # context menu
        self.cmenu = QtGui.QMenu()
        self.cmenu.addAction(self.actionDelete_selection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
                     self.show_context_menu)
        # make rulers' and modes buttons checkable
        self.actionSetVerticalRuler.setCheckable(True)
        self.actionSetHorizontalRuler.setCheckable(True)
        # add all zoom values
        self.zoom_comboBox.addItems(self.controller.get_all_zoom_values())
        # TODO rename it!!! changeIcons -> settings
        self.toolbarpart.changeIcons_button.setEnabled(True)
        self.toolbarpart.changeIcons_button.clicked.connect(
            self.change_settings)
        self.toolbarpart.autozone_button.setEnabled(False)
        self.toolbarpart.autozone_button.clicked.connect(self.autozones)
        # unfortunately could not assign actions as could not get rid of action
        # text displayed
        self.prevPage_button.clicked.connect(self.prev_page)
        self.prevPage_button.setShortcut(QtCore.Qt.Key_Left)
        self.nextPage_button.clicked.connect(self.next_page)
        self.nextPage_button.setShortcut(QtCore.Qt.Key_Right)
        self.toolbarpart.zoomIn_button.clicked.connect(self.zoom_in)
        self.toolbarpart.zoomOut_button.clicked.connect(self.zoom_out)
        self.toolBar.addWidget(self.toolbarpart.layoutWidget)
        # create progress bar for REALLY long operations (like saving every
        # page of heavy differently sized pdf)
        self.progress_bar = QtGui.QProgressBar(self.imageLabel)
        self.progress_text = QtGui.QLabel(u"", self.imageLabel)
        self.progress_bar.hide()
        self.progress_text.hide()
        self._set_appearance()
        # make window occupy all screen
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width() * 0.9, screen.height() * 0.9)
        # setup settings dialog
        self.settings_dialog = Settings(self.controller, self)

    def _fill_views(self):
        for mode in [self.SECTION_MODE, self.MARKUP_MODE]:
            self.toc_controller.fill_with_data(mode)

    def show_progress_bar(self, text):
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.BusyCursor))
        #self.progress_bar.show()
        #self.progress_text.show()
        #self.progress_text.setText(text)

    def hide_progress_bar(self):
        self.progress_bar.hide()
        #self.progress_text.setText(u"")
        self.progress_text.hide()
        QtGui.QApplication.restoreOverrideCursor()

    # all work on colors and buttons' styles done here
    def _set_appearance(self):
        # here come toolbuttons created in designer
        #load_pdf = self.toolBar.widgetForAction(self.actionLoad_pdf)
        #load_markup = self.toolBar.widgetForAction(self.actionLoad_markup)
        #save = self.toolBar.widgetForAction(self.actionSmartSave)
        #hor_ruler = self.toolBar.widgetForAction(self.actionSetHorizontalRuler)
        #vert_ruler = self.toolBar.widgetForAction(self.actionSetVerticalRuler)
        appearance = { self.toolbarpart.nextPage_button: 'buttons/Page_down',
                       self.toolbarpart.prevPage_button: 'buttons/Page_up',
                       self.toolbarpart.zoomIn_button: 'buttons/Plus',
                       self.toolbarpart.zoomOut_button: 'buttons/Minus',
                       self.toolbarpart.changeIcons_button: \
                          'buttons/Choose_icons'}
        menubuttons = {
            self.actionLoad_pdf: 'buttons/Load_file',
            self.actionLoad_markup: 'buttons/Load_markup',
            self.actionSmartSave: 'buttons/Save',
            self.actionSetHorizontalRuler: 'buttons/Vertical_ruler',
            self.actionSetVerticalRuler: 'buttons/Horisontal_ruler',
        }
        for (widget, iconfile) in menubuttons.items():
            self.generate_menubutton_stylesheet(widget, iconfile)
        for (widget, style) in appearance.items():
            widget.setStyleSheet(self.generate_toolbutton_stylesheet(style))
        # all other stylesheets come here
        self.totalPagesLabel.setStyleSheet(BLACK_LABEL_STYLESHEET)
        self.setStyleSheet(GENERAL_STYLESHEET)
        self.my_widget = QtGui.QWidget(self.centralwidget)
        self.layout_general = QtGui.QVBoxLayout(self.my_widget)
        self.layout_general.addWidget(self.toolBar)
        self.layout_general.addWidget(self.scrollArea)
        self.layout_general.addWidget(self.progress_bar)
        self.layout_general.addWidget(self.progress_text)
        self.layoutmain = QtGui.QHBoxLayout(self.centralwidget)
        self.layoutmain.addWidget(self.my_widget)
        self.layoutmain.addWidget(self.tabWidget)

    def _set_widgets_data_on_doc_load(self):
        self.spinBox.setValue(1)
        total_pages = self.controller.get_total_pages()
        self.spinBox.setRange(1, total_pages)
        self.actionLoad_markup.setEnabled(True)

    @property
    def mode(self):
        if self.tabWidget.currentIndex() == 0:
            return self.SECTION_MODE
        else:
            return self.MARKUP_MODE

    def autozones(self):
        self.show_progress_bar(u"Автоматическое размещение зон ...")
        num = self.controller.autozones(self.imageLabel)
        self.hide_progress_bar()

    def change_settings(self):
        result, settings = self.settings_dialog.show_settings()
        # save login anyway
        if settings["login"] != "":
            self.controller.login = settings["login"]
        if result:
            print "yes!"
            # have to validate received data
            # TODO cms-course id validation\smart-search
            for key in ["first-page", "cms-course", "margins"]:
                if settings[key] == "":
                    del settings[key]
            for key in ["start-autozones", "end-autozones",
                        "passthrough-zones"]:
                if settings[key] == []:
                    del settings[key]
            self.controller.settings_changed(settings)

    # mind that this is called every time a view is clicked, not only on
    # selection
    def on_selected(self):
        # always set normal mode for marks' creation
        self.set_normal_state()
        self.toc_controller.process_selected(self.mode)
        if self.toc_controller.active_elem:
            self.mark_to_navigate = self.controller.get_next_paragraph_mark(
                self.mode, self.mark_to_navigate)
        if self.mark_to_navigate:
            self.spinBox.setValue(self.mark_to_navigate.page)

    def on_tab_switched(self, new_tab):
        # deselect all previously selected elements
        self.controller.deselect_all()
        if new_tab == 0:
            self.controller.set_normal_section_mode()
            self.toolbarpart.autozone_button.setEnabled(False)
            self.actionSetVerticalRuler.setEnabled(True)
            self.actionSetHorizontalRuler.setEnabled(True)
        else:
            self.controller.set_normal_markup_mode()
            self.toolbarpart.autozone_button.setEnabled(True)
            self.actionSetVerticalRuler.setEnabled(False)
            self.actionSetHorizontalRuler.setEnabled(False)
        old_tab = (new_tab + 1) % 2
        self.toc_controller.process_mode_switch(self.TAB_MODE[old_tab],
                                                self.TAB_MODE[new_tab])

    # mind that every time currentIndex is changed on_zoom_value_changed is
    # called, so to eliminate double work have to check that delta is not 0
    def on_zoom_changed(self, scale):
        # set combo box value
        self.last_zoom_index = self.controller.get_current_zoom_index()
        self.zoom_comboBox.setCurrentIndex(self.last_zoom_index)

    def on_zoom_value_change(self):
        # calc delta, set widgets data and call zoom
        current = self.zoom_comboBox.currentIndex()
        delta = (current - self.last_zoom_index) * (self.controller.ZOOM_DELTA)
        if delta != 0 :
            self.last_zoom_index = current
            self.zoom_comboBox.setCurrentIndex(self.last_zoom_index)
            self.controller.zoom(delta, step_by_step=False)

    # context menu fill be shownn only if sth is selected at the moment
    def show_context_menu(self, point):
        self.last_right_click = self.mapToGlobal(point)
        self.cmenu.exec_(self.last_right_click)

    # delete currently selected marks on current page.
    def delete_marks(self):
        self.controller.delete_marks()

    # this is called when shift + del is pressed
    def delete_marks_forced(self):
        self.controller.delete_marks(forced=True)

    def delete_all(self):
        if not self.show_wipe_all_dialog():
            return
        self.controller.delete_all()

    def open_file(self):
        if self.controller.any_unsaved_changes and \
                not self.show_unsaved_data_dialog():
            return
        filename = QtGui.QFileDialog.getOpenFileName(
            self, QtCore.QString.fromUtf8(u'Загрузить учебник'), '.',
                                          'Pdf files (*.pdf)')
        if not filename:
            return
        self._fill_views()
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(
            QtCore.Qt.BusyCursor))
        result = self.controller.open_file(unicode(filename))
        QtGui.QApplication.restoreOverrideCursor()
        if not result:
            self.show_cant_open_dialog()
            return
        self._set_widgets_data_on_doc_load()
        # clear listView and fill again with appropriate for given course-id
        # data fetched from cas
        self.update()

    def load_markup(self):
        if self.controller.any_unsaved_changes and \
                not self.show_unsaved_data_dialog():
            return
        filename = QtGui.QFileDialog.\
            getOpenFileName(self,
                            QtCore.QString.fromUtf8(u'Загрузить разметку'),
                            '.',
                            "Xml files (*.xml *.unfinished)")
        if not filename:
            return
        self.last_open_doc_name = unicode(filename)
        # clear listView and fill again with appropriate for given course-id
        # data fetched from cas
        self._fill_views()
        self.show_progress_bar(u"Загрузка разметки ...")
        self.controller.load_markup(self.last_open_doc_name, self.imageLabel)
        # if markup no finished -> make sure that filename has unfinished
        # extension
        if not self.controller.markup_finished:
            name, ext = os.path.splitext(self.last_open_doc_name)
            self.last_open_doc_name = name + ".unfinished"
        self.hide_progress_bar()

    def save(self):
        if not self.last_open_doc_name:
            return
        if not self.controller.verify_mark_pairs():
            self.show_cant_save_dialog()
            return False
        self.show_progress_bar(u"Сохранение разметки ... ")
        self.controller.save(self.last_open_doc_name)
        print self.last_open_doc_name
        self.hide_progress_bar()

    def save_as(self):
        # check that all marked paragraphs have both marks
        if not self.controller.verify_mark_pairs():
            self.show_cant_save_dialog()
            return False
        filename = self.show_save_as_dialog()
        if not filename:
            return
        self.show_progress_bar(u"Сохранение разметки ... ")
        self.last_open_doc_name = self.controller.save(filename)
        self.hide_progress_bar()
        return True

    # depending on last_open_doc executes either save or save as
    def smart_save(self):
        self.save() if self.last_open_doc_name else self.save_as()

    # here 1st page has number 1
    # if there are any marks on page, highlight the corresponding paragraph of
    # the first met in the toc-list
    def go_to_page(self, pagenum):
        total_pages = self.controller.get_total_pages()
        if total_pages == 0:
            return
        if self.controller.go_to_page(pagenum):
            self.pageNum = pagenum
            self.nextPage_button.setEnabled(not self.pageNum == total_pages)
            self.prevPage_button.setEnabled(not self.pageNum == 1)
            self.update()
        # set total pages label text
        self.totalPagesLabel.setText(BookViewerWidget.TOTAL_PAGES_TEXT % \
                                     (self.pageNum, total_pages))
        marks = self.controller.get_page_marks(pagenum, self.mode)
        if marks != []:
            self.toc_controller.process_go_to_page(marks[0], self.mode)

    def navigate_to_first_error(self):
        error = self.controller.get_first_error_mark(self.mode)
        if error:
            error_page = self.toc_controller.\
                process_navigate_to_error(error, self.mode)
            self.go_to_page(error.page)

    def zoom_in(self):
        value = self.controller.zoom(self.controller.ZOOM_DELTA)
        self.on_zoom_changed(value)

    def zoom_out(self):
        value = self.controller.zoom(-self.controller.ZOOM_DELTA)
        self.on_zoom_changed(value)

    def set_normal_state(self):
        self.actionSetVerticalRuler.setChecked(False)
        self.actionSetHorizontalRuler.setChecked(False)
        # set normal state depending on current tab index
        if self.mode == self.SECTION_MODE:
            self.controller.set_normal_section_mode()
        else:
            self.controller.set_normal_markup_mode()

    def set_horizontal_ruler_state(self):
        self.actionSetVerticalRuler.setChecked(False)
        if self.actionSetHorizontalRuler.isChecked():
            self.actionSetHorizontalRuler.setChecked(True)
            self.controller.set_horizontal_ruler_mode()
        else:
            self.set_normal_state()

    def set_vertical_ruler_state(self):
        self.actionSetHorizontalRuler.setChecked(False)
        if self.actionSetVerticalRuler.isChecked():
            self.actionSetVerticalRuler.setChecked(True)
            self.controller.set_vertical_ruler_mode()
        else:
            self.set_normal_state()

    def next_page(self):
        self.spinBox.setValue(self.pageNum + 1)

    def prev_page(self):
        self.spinBox.setValue(self.pageNum - 1)

    def closeEvent(self, event):
        #if self.controller.any_unsaved_changes and \
                #not self.show_unsaved_data_dialog():
            #event.ignore()
        #else:
            event.accept()

    def update_console_data(self):
        msg = self.toc_controller.get_first_error_msg(self.mode)
        self.console.set_first_error_data(
                self.toc_controller.get_total_error_count(self.mode), msg)

    # only to be called from child
    def call_wheelEvent(self, event):
        if event.delta() > 0:
            self.prev_page()
        elif event.delta() < 0:
            self.next_page()

    def update(self):
        super(BookViewerWidget, self).update()
        # update console data
        # TODO it might not be here, think of a better place
        self.update_console_data()
        # set actions enabled\disabled depending on current situation
        anything_selected = self.controller.selected_marks_and_rulers != []
        self.actionDelete_selection.setEnabled(anything_selected)
        self.actionForced_delete_selection.setEnabled(anything_selected)
        self.actionDelete_all.setEnabled(self.controller.any_unsaved_changes)
        self.actionSave.setEnabled(self.last_open_doc_name is not None)

    ## all possible dialogs go here
    # general politics: returns True if can proceed with anything after
    # the func call, False if should return from any function
    def show_unsaved_data_dialog(self):
        if not self.unsaved_changes_dialog:
            self.unsaved_changes_dialog = QtGui.QMessageBox(self)
            self.unsaved_changes_dialog.setText(u"Документ был изменен.")
            self.unsaved_changes_dialog.setInformativeText(
                u"Хотите сохранить изменения?")
            self.unsaved_changes_dialog.setStandardButtons(
                QtGui.QMessageBox.Cancel |
                QtGui.QMessageBox.Discard |
                QtGui.QMessageBox.Save)
            self.unsaved_changes_dialog.setDefaultButton(QtGui.QMessageBox.Save)
        result = self.unsaved_changes_dialog.exec_()
        if result == QtGui.QMessageBox.Save:
            return self.save_as()
        elif result == QtGui.QMessageBox.Discard:
            return True
        elif result == QtGui.QMessageBox.Cancel:
            return False

    def show_cant_save_dialog(self):
        if not self.cant_save_dialog:
            self.cant_save_dialog = QtGui.QMessageBox(self)
            self.cant_save_dialog.setText(u"Невозможно сохранить изменения.")
            self.cant_save_dialog.setInformativeText(
                u"Не у всех размеченных параграфов есть метки начала и " + \
                u"конца в правильном порядке.")
            self.cant_save_dialog.setStandardButtons(QtGui.QMessageBox.Cancel)
        self.cant_save_dialog.exec_()

    def show_cant_open_dialog(self):
        if not self.cant_open_dialog:
            self.cant_open_dialog = QtGui.QMessageBox(self)
            self.cant_open_dialog.setText(u"Невозможно открыть файл.")
            self.cant_open_dialog.setInformativeText(
                u"Проверьте, что заданный файл является pdf-файлом.")
            self.cant_open_dialog.setStandardButtons(QtGui.QMessageBox.Cancel)
        self.cant_open_dialog.exec_()

    def show_wipe_all_dialog(self):
        if not self.wipe_all_dialog:
            self.wipe_all_dialog = QtGui.QMessageBox(self)
            self.wipe_all_dialog.setText(u"Удаление всех элементов разметки.")
            self.wipe_all_dialog.setInformativeText(
            u"Вы уверены, что хотите продолжить? Это действие нельзя отменить.")
            self.wipe_all_dialog.setStandardButtons(QtGui.QMessageBox.Yes |
                                                    QtGui.QMessageBox.No)
        result = self.wipe_all_dialog.exec_()
        if result == QtGui.QMessageBox.Yes:
            return True
        return False

    def show_save_as_dialog(self):
        if not self.save_as_dialog:
            self.save_as_dialog = QtGui.QFileDialog(self)
            self.save_as_dialog.setConfirmOverwrite(True)
            self.save_as_dialog.setWindowTitle(
                QtCore.QString.fromUtf8(u"Сохранить разметку"))
        extension = "xml" if self.controller.markup_finished else "unfinished"
        self.save_as_dialog.setDefaultSuffix(extension)
        self.save_as_dialog.setNameFilter("*." + extension)
        self.save_as_dialog.exec_()
        filename = self.save_as_dialog.selectedFiles()[0] \
            if self.save_as_dialog.selectedFiles() else None
        if not filename:
            return None
        filename = unicode(filename)
        # check if overwriting existing file
        if not self.file_exists_dialog:
            self.file_exists_dialog = QtGui.QMessageBox(self)
            self.file_exists_dialog.setText(u"Файл существует")
            self.file_exists_dialog.setInformativeText(
                u"Вы хотите перезаписать существующий файл?")
            self.file_exists_dialog.setStandardButtons(QtGui.QMessageBox.Yes |
                                                       QtGui.QMessageBox.No)
        if os.path.isfile(filename):
            result = self.file_exists_dialog.exec_()
            if result == QtGui.QMessageBox.Yes:
                return filename
            return None
        return filename
