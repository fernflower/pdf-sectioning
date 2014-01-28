#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from imagelabel import QImageLabel
from documentprocessor import DocumentProcessor, LoaderError

MAX_SCALE = 5
MIN_SCALE = 1


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    totalPagesText = "total %d out of %d"

    def __init__(self, cms_course_toc, doc_processor=None):
        super(BookViewerWidget, self).__init__()
        self.setupUi(self)
        self.dp = doc_processor
        # first page has number 1
        self.paragraphs = {}
        self.course_toc = cms_course_toc
        self.pageNum = 1
        self.scale = 1
        self._set_widgets_data_on_doc_load()
        self.init_actions()
        self.init_widgets()

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
        model = QtGui.QStandardItemModel()
        for elem in self.course_toc:
            item = QtGui.QStandardItem(elem["name"])
            item.setSelectable(True)
            model.appendRow(item)
        self.listView.setModel(model)

    def _set_widgets_data_on_doc_load(self):
        self.spinBox.setValue(1)
        if self.dp:
            self.spinBox.setRange(1, self.dp.totalPages)
            self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                         (1, self.dp.totalPages))

    @property
    def is_toc_selected(self):
        return self.get_selected_toc_elem() is not None

    def get_selected_toc_elem(self):
        selected = self.listView.selectedIndexes()
        if selected:
            return self.course_toc[selected[0].row()]

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '.')
        if not filename:
            return
        print "filename is %s" % unicode(filename)
        # check if any file open at the moment
        self.dp = DocumentProcessor(unicode(filename))
        self._set_widgets_data_on_start()
        self.update()

    def load_markup(self):
        if not self.dp:
            return
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'OpenFile',
                                                     '.',
                                                     "Xml files (*.xml)")
        if not filename:
            return
        raise NotImplementedError()

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
                para_key = m.toc_elem["cas-id"]
                mark = {"page" : m.page,
                        "name" : m.toc_elem["name"],
                        "y": self.transform_to_pdf_coords(m.geometry()).y()}
                try:
                    pdf_paragraphs[para_key].append(mark)
                except KeyError:
                    pdf_paragraphs[para_key] = [mark]
        if not self.dp:
            return
        dir_name = QtGui.QFileDialog.getExistingDirectory(self,
                                                          'Select Directory')
        if dir_name:
            self.dp.save_all(str(dir_name), pdf_paragraphs)

    # here 1st page has number 1
    def go_to_page(self, pagenum):
        if not self.dp:
            return
        # hide selections on this page
        if str(self.pageNum) in self.paragraphs.keys():
            map(lambda m:m.hide(), self.paragraphs[str(self.pageNum)])
        if str(pagenum) in self.paragraphs.keys():
            map(lambda m:m.show(), self.paragraphs[str(pagenum)])
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
            for page_key, markslist in self.paragraphs.items():
                for m in markslist:
                    m.adjust(new_scale / old_scale)

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

    # add paragraph mark (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[str(mark.page)]:
                self.paragraphs[str(mark.page)].append(mark)
        except KeyError:
            self.paragraphs[str(mark.page)] = [mark]

    def update_paragraphs(self, paragraph_marks):
        for cas_id, markslist in paragraph_marks.items():
            for mark in markslist:
                self.add_paragraph_mark(mark)
                #mark.pdf_coords = self.transform_to_pdf_coords(mark.geometry())

    def normalize_rect(self, rect):
        return QtCore.QRectF(rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return self.normalize_rect(rect)
