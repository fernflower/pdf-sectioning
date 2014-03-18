# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'add_zones.ui'
#
# Created: Tue Mar 18 16:02:37 2014
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

class Ui_addZones(object):
    def setupUi(self, addZones):
        addZones.setObjectName(_fromUtf8("addZones"))
        addZones.resize(631, 397)
        self.verticalLayout_4 = QtGui.QVBoxLayout(addZones)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label = QtGui.QLabel(addZones)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.allZones_listview = QtGui.QListView(addZones)
        self.allZones_listview.setObjectName(_fromUtf8("allZones_listview"))
        self.verticalLayout_2.addWidget(self.allZones_listview)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem1)
        self.add_button = QtGui.QPushButton(addZones)
        self.add_button.setDefault(False)
        self.add_button.setObjectName(_fromUtf8("add_button"))
        self.verticalLayout_3.addWidget(self.add_button)
        self.remove_button = QtGui.QPushButton(addZones)
        self.remove_button.setDefault(False)
        self.remove_button.setFlat(False)
        self.remove_button.setObjectName(_fromUtf8("remove_button"))
        self.verticalLayout_3.addWidget(self.remove_button)
        self.up_button = QtGui.QPushButton(addZones)
        self.up_button.setObjectName(_fromUtf8("up_button"))
        self.verticalLayout_3.addWidget(self.up_button)
        self.down_button = QtGui.QPushButton(addZones)
        self.down_button.setObjectName(_fromUtf8("down_button"))
        self.verticalLayout_3.addWidget(self.down_button)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem2)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem3)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_2 = QtGui.QLabel(addZones)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.chosenZones_listview = QtGui.QListView(addZones)
        self.chosenZones_listview.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
        self.chosenZones_listview.setObjectName(_fromUtf8("chosenZones_listview"))
        self.verticalLayout.addWidget(self.chosenZones_listview)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(addZones)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_4.addWidget(self.buttonBox)

        self.retranslateUi(addZones)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), addZones.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), addZones.reject)
        QtCore.QMetaObject.connectSlotsByName(addZones)

    def retranslateUi(self, addZones):
        addZones.setWindowTitle(_translate("addZones", "Dialog", None))
        self.label.setText(_translate("addZones", "Доступные типы зон", None))
        self.add_button.setText(_translate("addZones", "add", None))
        self.remove_button.setText(_translate("addZones", "remove", None))
        self.up_button.setText(_translate("addZones", "up", None))
        self.down_button.setText(_translate("addZones", "down", None))
        self.label_2.setText(_translate("addZones", "Выбранные зоны", None))

