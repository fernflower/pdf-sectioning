#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
from docwidget import Ui_MainWindow
from documentprocessor import DocumentProcessor, LoaderError


class BookViewerWidget(QtGui.QMainWindow, Ui_MainWindow):
    totalPagesText = "total"

    def __init__(self, doc_processor=None):
        super(BookViewerWidget, self).__init__()
        self.dp = doc_processor
        self.setupUi(self)
        self.init_actions()

    def init_actions(self):
        self.actionLoad_pdf.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save)
        self.actionLoad_markup.triggered.connect(self.load_markup)
        self.prevPage_button.clicked.connect(self.prev_page)
        self.nextPage_button.clicked.connect(self.next_page)
        self.spinBox.connect(self.spinBox,
                             QtCore.SIGNAL("valueChanged(int)"),
                             self.go_to_page)

    def _set_widgets_data_on_start(self):
        self.spinBox.setValue(1)
        if self.dp:
            self.spinBox.setRange(1, self.dp.totalPages)
            self.totalPagesLabel.setText(BookViewerWidget.totalPagesText % \
                                         (1, self.dp.totalPages))
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

    def save(self):
        raise NotImplementedError()

    # here 1st page has number 1
    def go_to_page(self, pagenum):
        if not self.dp:
            return
        if self.dp.go_to_page(pagenum - 1):
            self.pageNum = pagenum
            self.update()

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
