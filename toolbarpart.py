# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ToolBarPart.ui'
#
# Created: Wed Feb 12 20:36:10 2014
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

class Ui_ToolBarPart(object):
    def setupUi(self, ToolBarPart):
        ToolBarPart.setObjectName(_fromUtf8("ToolBarPart"))
        ToolBarPart.resize(1661, 331)
        self.widget = QtGui.QWidget(ToolBarPart)
        self.widget.setGeometry(QtCore.QRect(0, 30, 610, 27))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(13, 22, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.changeIcons_button = QtGui.QToolButton(self.widget)
        self.changeIcons_button.setObjectName(_fromUtf8("changeIcons_button"))
        self.horizontalLayout.addWidget(self.changeIcons_button)
        self.autozone_button = QtGui.QPushButton(self.widget)
        self.autozone_button.setFlat(True)
        self.autozone_button.setObjectName(_fromUtf8("autozone_button"))
        self.horizontalLayout.addWidget(self.autozone_button)
        spacerItem1 = QtGui.QSpacerItem(18, 22, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.prevPage_button = QtGui.QToolButton(self.widget)
        self.prevPage_button.setText(_fromUtf8(""))
        self.prevPage_button.setCheckable(False)
        self.prevPage_button.setObjectName(_fromUtf8("prevPage_button"))
        self.horizontalLayout.addWidget(self.prevPage_button)
        self.nextPage_button = QtGui.QToolButton(self.widget)
        self.nextPage_button.setText(_fromUtf8(""))
        self.nextPage_button.setObjectName(_fromUtf8("nextPage_button"))
        self.horizontalLayout.addWidget(self.nextPage_button)
        self.pagesSpinBox = QtGui.QSpinBox(self.widget)
        self.pagesSpinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.pagesSpinBox.setObjectName(_fromUtf8("pagesSpinBox"))
        self.horizontalLayout.addWidget(self.pagesSpinBox)
        self.totalPages_label = QtGui.QLabel(self.widget)
        self.totalPages_label.setObjectName(_fromUtf8("totalPages_label"))
        self.horizontalLayout.addWidget(self.totalPages_label)
        spacerItem2 = QtGui.QSpacerItem(28, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.zoomIn_button = QtGui.QToolButton(self.widget)
        self.zoomIn_button.setObjectName(_fromUtf8("zoomIn_button"))
        self.horizontalLayout.addWidget(self.zoomIn_button)
        self.zoomOut_button = QtGui.QToolButton(self.widget)
        self.zoomOut_button.setObjectName(_fromUtf8("zoomOut_button"))
        self.horizontalLayout.addWidget(self.zoomOut_button)
        spacerItem3 = QtGui.QSpacerItem(13, 22, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.zoomComboBox = QtGui.QComboBox(self.widget)
        self.zoomComboBox.setObjectName(_fromUtf8("zoomComboBox"))
        self.horizontalLayout.addWidget(self.zoomComboBox)
        spacerItem4 = QtGui.QSpacerItem(58, 22, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.onePage_button = QtGui.QToolButton(self.widget)
        self.onePage_button.setCheckable(True)
        self.onePage_button.setObjectName(_fromUtf8("onePage_button"))
        self.horizontalLayout.addWidget(self.onePage_button)
        self.twoPage_button = QtGui.QToolButton(self.widget)
        self.twoPage_button.setCheckable(True)
        self.twoPage_button.setObjectName(_fromUtf8("twoPage_button"))
        self.horizontalLayout.addWidget(self.twoPage_button)

        self.retranslateUi(ToolBarPart)
        QtCore.QMetaObject.connectSlotsByName(ToolBarPart)

    def retranslateUi(self, ToolBarPart):
        ToolBarPart.setWindowTitle(_translate("ToolBarPart", "Form", None))
        self.autozone_button.setText(_translate("ToolBarPart", "Autozone", None))
        self.totalPages_label.setText(_translate("ToolBarPart", "0 of 0", None))
