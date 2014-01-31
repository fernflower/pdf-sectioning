#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from imagelabel import QImageLabel
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import make_paragraph_mark
from tocelem import QTocElem


MAX_SCALE = 5
MIN_SCALE = 1


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    totalPagesText = "total %d out of %d"

    def __init__(self, cms_course_toc, doc_processor=None):
        super(BookViewerWidget, self).__init__()
        self.setupUi(self)
        self.dp = doc_processor
        self.last_right_click = None
        # first page has number 1
        self.paragraphs = {}
        self.course_toc = cms_course_toc
        self.pageNum = 1
        self.scale = 1
        self._set_widgets_data_on_doc_load()
        self.init_actions()
        self.init_widgets()

    def selected_marks(self):
        return [m for m in self.get_current_page_marks() if m.is_selected]

    def init_actions(self):
        self.actionLoad_pdf.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save)
        self.actionLoad_markup.triggered.connect(self.load_markup)
        self.prevPage_button.clicked.connect(self.prev_page)
        self.nextPage_button.clicked.connect(self.next_page)
        self.spinBox.connect(self.spinBox,
                             QtCore.SIGNAL("valueChanged(int)"),
                             self.go_to_page)

    def init_widgets(self):
        # add image label
        self.imageLabel = QImageLabel(self, self)
        self.imageLabel.setScaledContents(True)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setGeometry(self.scrollArea.x(),
                                    self.scrollArea.y(),
                                    self.frameSize().width(),
                                    self.frameSize().height())
        # show toc elems
        self._fill_listview(self.course_toc)
        self.imageLabel.setFocus(True)
        self.listView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.listView.selectionModel().selectionChanged.connect(
            self.on_selection_change)
        # context menu
        self.cmenu = QtGui.QMenu()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.actionDelete_selection = \
            self.cmenu.addAction("Delete paragraph mark")
        self.actionDelete_selection.triggered.connect(
            self._delete_mark)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
                     self.show_context_menu)

    def _set_widgets_data_on_doc_load(self):
        self.spinBox.setValue(1)
        if self.dp:
            self.spinBox.setRange(1, self.dp.totalPages)
            self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                         (1, self.dp.totalPages))

    def on_selection_change(self):
        current = self.get_selected_toc_elem()
        if not current.is_not_started():
            (start_mark, end_mark) = \
                self.imageLabel.paragraph_marks[current.cas_id]
            page_goto = next(
                (mark.page for mark in [start_mark, end_mark] if mark), None)
            # navigate to page where start mark is
            if page_goto:
                # only have to change spinbox value: the connected signal will
                # do all work automatically
                self.spinBox.setValue(page_goto)

    def show_context_menu(self, point):
        self.last_right_click = self.mapToGlobal(point)
        self.cmenu.exec_(self.last_right_click)

    # delete currently selected mark. Mark is always on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def _delete_mark(self):
        selected = self.imageLabel.find_selected(self.last_right_click)
        if selected:
            self.paragraphs[str(self.pageNum)].remove(selected)
            self.imageLabel.delete_mark(selected)
            selected.destroy()

    def _fill_listview(self, items):
        # show toc elems
        model = self.listView.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for i, elem in enumerate(items):
            item = QTocElem(elem["name"], elem["cas-id"], i)
            model.appendRow(item)
        self.listView.setModel(model)

    # should be here to navigate regardless of focused widget (imagelabel or
    # listview)
    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_PageDown]:
            self.prev_page()
        elif event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_PageUp]:
            self.next_page()
        self.update()

    @property
    def is_toc_selected(self):
        return self.get_selected_toc_elem() is not None

    def get_selected_toc_elem(self):
        model = self.listView.model()
        selected_idx = self.listView.currentIndex()
        if selected_idx:
            return model.itemFromIndex(selected_idx)

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_toc_elem(self, cas_id):
        def find():
            for i, elem in enumerate(self.course_toc):
                if elem["cas-id"] == cas_id:
                    return i
            return -1
        order_num = find()
        if order_num != -1:
            return self.listView.model().item(order_num)

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '.')
        if not filename:
            return
        #TODO dialog with warning if any file open at the moment
        self.dp = DocumentProcessor(unicode(filename))
        self._set_widgets_data_on_start()
        self.update()

    def load_markup(self):
        # TODO dialog with warning that all data that has not been saved will
        # be lost
        if not self.dp:
            return
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'OpenFile',
                                                     '.',
                                                     "Xml files (*.xml)")
        if not filename:
            return
        # destroy previous data
        for page, marks in self.paragraphs.items():
            map(lambda m: m.destroy(), marks)
        self.paragraphs = {}
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # clear listView and fill again with appropriate for given course-id
        # data fetched from cas
        self._fill_listview(self.course_toc)
        # generate start\end marks from paragraphs' data
        for i, (cas_id, marks) in enumerate(paragraphs.items()):
            for m in marks:
                str_page = m["page"]
                mark = make_paragraph_mark(parent=self.imageLabel,
                                           cas_id=cas_id,
                                           name=m["name"],
                                           pos=QtCore.QPoint(0, float(m["y"])),
                                           page=int(str_page),
                                           toc_num=i,
                                           type=m["type"])
                mark.adjust(self.scale)
                # mark loaded paragraphs gray
                # TODO think how to eliminate calling this func twice
                elem = self.get_toc_elem(cas_id)
                if elem:
                    elem.mark_finished()
                if mark.page != self.pageNum:
                    mark.hide()
                try:
                    self.paragraphs[str_page].append(mark)
                except KeyError:
                    self.paragraphs[str_page] = [mark]
        self.imageLabel.reload_markup(self.paragraphs)

    def get_image(self):
        if not self.dp:
            return None
        res = self.dp.curr_page(self.scale)
        return res

    def save(self):
        # normalize to get pdf-coordinates (save with scale=1.0)
        pdf_paragraphs = {}
        for key, markslist in self.paragraphs.items():
            for m in markslist:
                para_key = m.cas_id
                mark = {"page" : m.page,
                        "name" : m.name,
                        "y": self.transform_to_pdf_coords(m.geometry()).y()}
                try:
                    pdf_paragraphs[para_key].append(mark)
                except KeyError:
                    pdf_paragraphs[para_key] = [mark]
        # check that all marked paragraphs have both marks
        if not self.imageLabel.verify_mark_pairs():
            QtGui.QMessageBox.warning(self, "Warning",
                                      "The result won't be saved " + \
                                      "as some paragraphs don't have END marks")
            return
        dir_name = QtGui.QFileDialog.getExistingDirectory(self,
                                                          'Select Directory')
        if not self.dp:
            return
        if dir_name:
            self.dp.save_all(str(dir_name), pdf_paragraphs)

    # here 1st page has number 1
    def go_to_page(self, pagenum):
        if not self.dp:
            return
        # hide selections on this page
        if str(self.pageNum) in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[str(self.pageNum)])
        # show selections on page we are switching to
        if str(pagenum) in self.paragraphs.keys():
            map(lambda m: m.show(), self.paragraphs[str(pagenum)])
        if self.dp.go_to_page(pagenum - 1):
            self.pageNum = pagenum
            self.update()

    def zoom(self, delta):
        new_scale = old_scale = self.scale
        if delta > 0:
            new_scale = self.scale + 0.5
        elif delta < 0:
            new_scale = self.scale - 0.5
        if new_scale >= MIN_SCALE and new_scale <= MAX_SCALE:
            self.scale = new_scale
            coeff = new_scale / old_scale
            for page_key, markslist in self.paragraphs.items():
                for m in markslist:
                    m.adjust(coeff)

    def next_page(self):
        self.spinBox.setValue(self.pageNum + 1)
        nextNum = self.spinBox.value()
        self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                     (nextNum, self.dp.totalPages))
        self.nextPage_button.setEnabled(not nextNum == self.dp.totalPages)
        self.prevPage_button.setEnabled(not nextNum == 1)

    def prev_page(self):
        self.spinBox.setValue(self.pageNum - 1)
        nextNum = self.spinBox.value()
        self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                     (nextNum, self.dp.totalPages))
        self.nextPage_button.setEnabled(not nextNum == self.dp.totalPages)
        self.prevPage_button.setEnabled(not nextNum == 1)

    def get_current_page_marks(self):
        try:
            return self.paragraphs[str(self.pageNum)]
        except KeyError:
            return []

    # add paragraph mark (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[str(mark.page)]:
                self.paragraphs[str(mark.page)].append(mark)
        except KeyError:
            self.paragraphs[str(mark.page)] = [mark]

    def update_paragraphs(self, paragraph_marks):
        for cas_id, (start, end) in paragraph_marks.items():
            if start is not None:
                self.add_paragraph_mark(start)
                if end is not None:
                    self.add_paragraph_mark(end)

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return QtCore.QRectF(
                      rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)
