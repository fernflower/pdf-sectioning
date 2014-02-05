#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from imagelabel import QImageLabel


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    totalPagesText = "total %d out of %d"

    def __init__(self, controller):
        super(BookViewerWidget, self).__init__()
        self.setupUi(self)
        self.controller = controller
        self.last_right_click = None
        self.pageNum = 1
        self._set_widgets_data_on_doc_load()
        self.init_actions()
        self.init_widgets()

    def init_actions(self):
        self.actionLoad_pdf.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save)
        self.actionLoad_markup.triggered.connect(self.load_markup)
        self.actionSetVerticalRuler.triggered.connect(
            self.set_vertical_ruler_state)
        self.actionSetHorizontalRuler.triggered.connect(
            self.set_horizontal_ruler_state)
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
            first_mark = self.controller.\
                get_first_paragraph_mark(current.cas_id)
            # navigate to page where start mark is
            if first_mark:
                # only have to change spinbox value: the connected signal will
                # do all work automatically
                self.spinBox.setValue(first_mark.page)

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
        filename = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '.')
        if not filename:
            return
        #TODO dialog with warning if any file open at the moment
        self.controller.open_file(unicode(filename))
        self._set_widgets_data_on_doc_load()
        self.update()

    def load_markup(self):
        # TODO dialog with warning that all data that has not been saved will
        # be lost
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'OpenFile',
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
            QtGui.QMessageBox.warning(self, "Warning",
                                      "The result won't be saved " + \
                                      "as some paragraphs don't have END marks")
            return
        dir_name = QtGui.QFileDialog.getExistingDirectory(self,
                                                          'Select Directory')
        if not dir_name:
            return
        self.controller.save(unicode(dir_name))

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
