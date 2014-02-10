#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from imagelabel import QImageLabel


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    totalPagesText = u"%d из %d"
    stylesheet = \
        """
        QMainWindow { background: rgb(83, 83, 83);}
        QScrollArea { background-color: rgb(58, 56, 56);
                      border: 1px solid black }
        QScrollBar:horizontal, QScrollBar:vertical
        {
            border: 2px solid grey;
            background: gray;
        }
        QScrollBar::add-page, QScrollBar::sub-page
        {
          background: none;
        }
        QListView { background: rgb(81, 81, 81);}
        QListView::item:selected { background: rgb(10, 90, 160); }
        QListView::item { color: rgb(230, 230, 230);
                          border-bottom: 0.5px solid rgb(58, 56, 56);
                        }
        QListView::item::icon {
          padding: 7px;
        }
        QSpinBox {background-color: rgb(58, 56, 56);
                  color: rgb(235, 235, 235)}
        """

    def __init__(self, controller):
        super(BookViewerWidget, self).__init__()
        self.setupUi(self)
        self.controller = controller
        self.last_right_click = None
        self.pageNum = 1
        # in order to implement navigation on toc-elem click. Store last mark
        # navigated to here
        self.mark_to_navigate = None
        # dialogs
        self.unsaved_changes_dialog = None
        self.cant_save_dialog = None
        self._set_widgets_data_on_doc_load()
        self.init_actions()
        self.init_widgets()

    def generate_toolbutton_stylesheet(self, button_name):
        return  \
            """
            QToolButton {
                        border: none;
                        background: url(%s.png) top center no-repeat;
            }
            QToolButton:hover {
                background: url(%s_hover.png) top center no-repeat;
                color: blue;
            }
            QToolButton:pressed, QToolButton:checked {
                        background: url(%s_pressed.png) top center no-repeat;
                        color: gray;}
        """ % (button_name, button_name, button_name)

    def init_actions(self):
        self.actionLoad_pdf.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save)
        self.actionLoad_markup.triggered.connect(self.load_markup)
        self.actionSetVerticalRuler.triggered.connect(
            self.set_vertical_ruler_state)
        self.actionSetHorizontalRuler.triggered.connect(
            self.set_horizontal_ruler_state)
        self.actionPrev_page.triggered.connect(self.prev_page)
        self.actionNext_page.triggered.connect(self.next_page)
        self.prevPage_button.clicked.connect(self.prev_page)
        self.nextPage_button.clicked.connect(self.next_page)
        self.spinBox.connect(self.spinBox,
                             QtCore.SIGNAL("valueChanged(int)"),
                             self.go_to_page)

    def init_widgets(self):
        # add image label
        self.imageLabel = QImageLabel(self, self.controller)
        self.imageLabel.setScaledContents(True)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setGeometry(self.scrollArea.x(),
                                    self.scrollArea.y(),
                                    self.frameSize().width(),
                                    self.frameSize().height())
        # show toc elems
        self._fill_listview()
        self.setFocus(True)
        self.listView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.listView.clicked.connect(self.on_selection_change)
        # context menu
        self.cmenu = QtGui.QMenu()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.actionDelete_selection = \
            self.cmenu.addAction("Delete")
        self.actionDelete_selection.triggered.connect(
            self.delete_marks)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
                     self.show_context_menu)
        # make rulers' buttons checkable
        self.actionSetVerticalRuler.setCheckable(True)
        self.actionSetHorizontalRuler.setCheckable(True)
        # colors and buttons
        self._set_appearance()

    def _set_appearance(self):
        self.setStyleSheet(self.stylesheet)
        self.prevPage_button.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Page_up'))
        self.nextPage_button.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Page_down'))
        # toolbar buttons
        load_pdf = self.toolBar.widgetForAction(self.actionLoad_pdf)
        load_pdf.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Load_file'))
        load_markup = self.toolBar.widgetForAction(self.actionLoad_markup)
        load_markup.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Load_markup'))
        save = self.toolBar.widgetForAction(self.actionSave)
        save.setStyleSheet(self.generate_toolbutton_stylesheet('buttons/Save'))
        hor_ruler = self.toolBar.widgetForAction(self.actionSetHorizontalRuler)
        hor_ruler.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Upper_border'))
        vert_ruler = self.toolBar.widgetForAction(self.actionSetVerticalRuler)
        # TODO substitute with an appropriate pic
        vert_ruler.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Lower_border'))
        prev_page = self.toolBar.widgetForAction(self.actionPrev_page)
        prev_page.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Page_up'))
        next_page = self.toolBar.widgetForAction(self.actionNext_page)
        next_page.setStyleSheet(
            self.generate_toolbutton_stylesheet('buttons/Page_down'))
        # total pages text set to white without affecting QRubberBand
        self.totalPagesLabel.setStyleSheet("QLabel {color: rgb(235, 235, 235)}")

    def _set_widgets_data_on_doc_load(self):
        self.spinBox.setValue(1)
        total_pages = self.controller.get_total_pages()
        self.spinBox.setRange(1, total_pages)
        self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                     (1, total_pages))

    def on_selection_change(self):
        # always set normal mode for marks' creation
        self.set_normal_state()
        current = self.get_selected_toc_elem()
        if current and not current.is_not_started():
            self.mark_to_navigate = self.controller.\
                get_next_paragraph_mark(current.cas_id, self.mark_to_navigate)
            # only have to change spinbox value: the connected signal will
            # do all work automatically
            if self.mark_to_navigate:
                self.spinBox.setValue(self.mark_to_navigate.page)

    # context menu fill be shownn only if sth is selected at the moment
    def show_context_menu(self, point):
        self.last_right_click = self.mapToGlobal(point)
        if self.controller.selected_marks_and_rulers() != []:
            self.cmenu.exec_(self.last_right_click)

    # delete currently selected marks on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def delete_marks(self):
        self.controller.delete_marks()

    def _fill_listview(self):
        # show toc elems
        model = self.listView.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for item in self.controller.create_toc_elems():
            model.appendRow(item)
        self.listView.setModel(model)

    # should be here to navigate regardless of focused widget (imagelabel or
    # listview)
    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_PageDown]:
            self.prev_page()
        elif event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_PageUp]:
            self.next_page()
        elif event.key() == QtCore.Qt.Key_Delete:
            self.delete_marks()
        self.update()

    def get_selected_toc_elem(self):
        model = self.listView.model()
        selected_idx = self.listView.currentIndex()
        if selected_idx:
            elem = model.itemFromIndex(selected_idx)
            self.controller.set_current_toc_elem(elem)
            return elem

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_toc_elem(self, cas_id):
        return self.controller.get_toc_elem(cas_id)

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            self, QtCore.QString.fromUtf8(u'Загрузить учебник'), '.')
        if not filename:
            return
        #TODO dialog with warning if any file open at the moment
        self.controller.open_file(unicode(filename))
        self._set_widgets_data_on_doc_load()
        self.update()

    def load_markup(self):
        if self.controller.any_unsaved_changes and \
                not self.show_unsaved_data_dialog():
            return
        filename = QtGui.QFileDialog.\
            getOpenFileName(self,
                            QtCore.QString.fromUtf8(u'Загрузить разметку'),
                            '.',
                            "Xml files (*.xml)")
        if not filename:
            return
        # clear listView and fill again with appropriate for given course-id
        # data fetched from cas
        self._fill_listview()
        self.controller.load_markup(unicode(filename), self.imageLabel)

    def save(self):
        # check that all marked paragraphs have both marks
        if not self.controller.verify_mark_pairs():
            self.show_cant_save_dialog()
            return False
        dir_name = QtGui.QFileDialog.\
            getExistingDirectory(self,
                                 QtCore.QString.fromUtf8(u'Сохранить разметку'))
        if not dir_name:
            return
        self.controller.save(unicode(dir_name))
        return True

    # here 1st page has number 1
    def go_to_page(self, pagenum):
        if self.controller.get_total_pages() == 0:
            return
        # hide selections on this page
        self.controller.hide_page_marks(self.pageNum)
        # show selections on page we are switching to
        self.controller.show_page_marks(pagenum)
        if self.controller.go_to_page(pagenum - 1):
            self.pageNum = pagenum
            self.update()

    def zoom(self, delta):
        return self.controller.zoom(delta)

    def set_normal_state(self):
        self.actionSetVerticalRuler.setChecked(False)
        self.actionSetHorizontalRuler.setChecked(False)
        self.controller.set_normal_mode()

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
        total_pages = self.controller.get_total_pages()
        self.spinBox.setValue(self.pageNum + 1)
        nextNum = self.spinBox.value()
        self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                     (nextNum, total_pages))
        self.nextPage_button.setEnabled(not nextNum == total_pages)
        self.prevPage_button.setEnabled(not nextNum == 1)

    def prev_page(self):
        total_pages = self.controller.get_total_pages()
        self.spinBox.setValue(self.pageNum - 1)
        nextNum = self.spinBox.value()
        self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                     (nextNum, total_pages))
        self.nextPage_button.setEnabled(not nextNum == total_pages)
        self.prevPage_button.setEnabled(not nextNum == 1)

    def get_current_page_marks(self):
        return self.controller.get_page_marks(self.pageNum)

    def closeEvent(self, event):
        if self.controller.any_unsaved_changes and \
                not self.show_unsaved_data_dialog():
            event.ignore()
        else:
            event.accept()

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
            return self.save()
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
