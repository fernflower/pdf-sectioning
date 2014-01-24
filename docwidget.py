# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout.ui'
#
# Created: Fri Jan 24 21:05:47 2014
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1035, 559)
        MainWindow.setFocusPolicy(QtCore.Qt.NoFocus)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setMinimumSize(QtCore.QSize(50, 30))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.prevPage_button = QtGui.QToolButton(self.widget)
        self.prevPage_button.setArrowType(QtCore.Qt.LeftArrow)
        self.prevPage_button.setObjectName(_fromUtf8("prevPage_button"))
        self.horizontalLayout_2.addWidget(self.prevPage_button)
        self.spinBox = QtGui.QSpinBox(self.widget)
        self.spinBox.setMaximumSize(QtCore.QSize(50, 16777215))
        self.spinBox.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.spinBox.setMouseTracking(False)
        self.spinBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.spinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.spinBox.setObjectName(_fromUtf8("spinBox"))
        self.horizontalLayout_2.addWidget(self.spinBox)
        self.nextPage_button = QtGui.QToolButton(self.widget)
        self.nextPage_button.setArrowType(QtCore.Qt.RightArrow)
        self.nextPage_button.setObjectName(_fromUtf8("nextPage_button"))
        self.horizontalLayout_2.addWidget(self.nextPage_button)
        self.totalPagesLabel = QtGui.QLabel(self.widget)
        self.totalPagesLabel.setObjectName(_fromUtf8("totalPagesLabel"))
        self.horizontalLayout_2.addWidget(self.totalPagesLabel)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addWidget(self.widget)
        self.scrollArea = QtGui.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 749, 424))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.horizontalLayout_5.addLayout(self.verticalLayout_2)
        self.listView = QtGui.QListView(self.centralwidget)
        self.listView.setObjectName(_fromUtf8("listView"))
        self.horizontalLayout_5.addWidget(self.listView)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1035, 20))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionLoad_pdf = QtGui.QAction(MainWindow)
        self.actionLoad_pdf.setObjectName(_fromUtf8("actionLoad_pdf"))
        self.actionPrev_page = QtGui.QAction(MainWindow)
        self.actionPrev_page.setObjectName(_fromUtf8("actionPrev_page"))
        self.actionNext_page = QtGui.QAction(MainWindow)
        self.actionNext_page.setObjectName(_fromUtf8("actionNext_page"))
        self.actionSave = QtGui.QAction(MainWindow)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionLoad_markup = QtGui.QAction(MainWindow)
        self.actionLoad_markup.setObjectName(_fromUtf8("actionLoad_markup"))
        self.toolBar.addAction(self.actionLoad_pdf)
        self.toolBar.addAction(self.actionLoad_markup)
        self.toolBar.addAction(self.actionSave)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.prevPage_button.setText(_translate("MainWindow", "prev", None))
        self.nextPage_button.setText(_translate("MainWindow", "next", None))
        self.totalPagesLabel.setText(_translate("MainWindow", "(page 0 from 0)", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.actionLoad_pdf.setText(_translate("MainWindow", "load file", None))
        self.actionLoad_pdf.setToolTip(_translate("MainWindow", "Загрузить pdf", None))
        self.actionPrev_page.setText(_translate("MainWindow", "prev page", None))
        self.actionNext_page.setText(_translate("MainWindow", "next page", None))
        self.actionSave.setText(_translate("MainWindow", "save", None))
        self.actionLoad_markup.setText(_translate("MainWindow", "load markup", None))

