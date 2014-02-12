#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from tocelem import QTocElem


class QConsole(QtGui.QWidget):
    COUNT_ERRORS_TEXT = u"%d ошибок"
    EVERYTHING_OK = u"Пока все хорошо"
    WRONG_ORDER = u"Ошибка в разметке: %s - конец параграфа стоит выше начала"
    # stylesheets section
    ERROR_COUNT_STYLESHEET_DFLT = \
        """
            QPushButton { background-color: rgb(0, 51, 153);
                          color: rgb(235, 235, 235)}
        """
    ERROR_COUNT_STYLESHEET_ERR = \
        """
            QPushButton { background-color: rgb(227, 58, 13);
                          color: rgb(235, 235, 235)}
        """

    ERROR_DATA_STYLESHEET = \
        """
            QLabel { color: rgb(235, 235, 235)}
        """

    def __init__(self, parent, parent_layout, bookviewer):
        super(QConsole, self).__init__()
        self.bookviewer = bookviewer
        self.errors_count = QtGui.QPushButton(parent)
        self.errors_count.setText(self.COUNT_ERRORS_TEXT % 0)
        self.errors_count.setMaximumSize(QtCore.QSize(70, 30))
        self.errors_count.clicked.connect(self.errors_clicked)
        self.errors_data = QtGui.QLabel(parent)
        self.errors_data.setText(self.EVERYTHING_OK)
        # now bind to layout
        self.consoleLayout = QtGui.QHBoxLayout()
        self.consoleLayout.addWidget(self.errors_count)
        self.consoleLayout.addWidget(self.errors_data)
        # add all to parent layout
        parent_layout.addLayout(self.consoleLayout)
        # now set appearance
        self.errors_count.setStyleSheet(self.ERROR_COUNT_STYLESHEET_DFLT)
        self.errors_data.setStyleSheet(self.ERROR_DATA_STYLESHEET)

    def set_error_count(self, count):
        self.update()

    def set_first_error_data(self, total_errors, message):
        if total_errors == 0:
            self.errors_count.setStyleSheet(self.ERROR_COUNT_STYLESHEET_DFLT)
        else:
            self.errors_count.setStyleSheet(self.ERROR_COUNT_STYLESHEET_ERR)
        self.errors_count.setText(self.COUNT_ERRORS_TEXT % total_errors)
        self.errors_data.setText(message)

    def update(self):
        self.errors_count.update()
        self.errors_data.update()

    def errors_clicked(self):
        self.bookviewer.navigate_to_first_error()
