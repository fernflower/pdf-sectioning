# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created: Tue Apr  1 16:16:47 2014
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(650, 429)
        self.verticalLayout_10 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_10.setObjectName(_fromUtf8("verticalLayout_10"))
        self.settings_tabs = QtGui.QTabWidget(Dialog)
        self.settings_tabs.setEnabled(True)
        self.settings_tabs.setObjectName(_fromUtf8("settings_tabs"))
        self.userData_tab = QtGui.QWidget()
        self.userData_tab.setObjectName(_fromUtf8("userData_tab"))
        self.verticalLayout_11 = QtGui.QVBoxLayout(self.userData_tab)
        self.verticalLayout_11.setObjectName(_fromUtf8("verticalLayout_11"))
        spacerItem = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem)
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.verticalLayout_5 = QtGui.QVBoxLayout()
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.label_4 = QtGui.QLabel(self.userData_tab)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.horizontalLayout_8.addWidget(self.label_4)
        self.verticalLayout_5.addLayout(self.horizontalLayout_8)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem1)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.label_5 = QtGui.QLabel(self.userData_tab)
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.horizontalLayout_7.addWidget(self.label_5)
        self.verticalLayout_5.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_9.addLayout(self.verticalLayout_5)
        self.verticalLayout_7 = QtGui.QVBoxLayout()
        self.verticalLayout_7.setObjectName(_fromUtf8("verticalLayout_7"))
        self.verticalLayout_6 = QtGui.QVBoxLayout()
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.login_edit = QtGui.QLineEdit(self.userData_tab)
        self.login_edit.setObjectName(_fromUtf8("login_edit"))
        self.verticalLayout_6.addWidget(self.login_edit)
        self.incorrectData_label = QtGui.QLabel(self.userData_tab)
        self.incorrectData_label.setStyleSheet(_fromUtf8("color: rgb(145, 30, 66)"))
        self.incorrectData_label.setObjectName(_fromUtf8("incorrectData_label"))
        self.verticalLayout_6.addWidget(self.incorrectData_label)
        self.verticalLayout_7.addLayout(self.verticalLayout_6)
        self.password_edit = QtGui.QLineEdit(self.userData_tab)
        self.password_edit.setObjectName(_fromUtf8("password_edit"))
        self.verticalLayout_7.addWidget(self.password_edit)
        self.horizontalLayout_9.addLayout(self.verticalLayout_7)
        self.verticalLayout_11.addLayout(self.horizontalLayout_9)
        spacerItem2 = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem2)
        spacerItem3 = QtGui.QSpacerItem(20, 12, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem3)
        spacerItem4 = QtGui.QSpacerItem(20, 37, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem4)
        spacerItem5 = QtGui.QSpacerItem(20, 25, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem5)
        spacerItem6 = QtGui.QSpacerItem(20, 12, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem6)
        spacerItem7 = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem7)
        spacerItem8 = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem8)
        spacerItem9 = QtGui.QSpacerItem(20, 26, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem9)
        self.settings_tabs.addTab(self.userData_tab, _fromUtf8(""))
        self.bookData_tab = QtGui.QWidget()
        self.bookData_tab.setObjectName(_fromUtf8("bookData_tab"))
        self.verticalLayout_16 = QtGui.QVBoxLayout(self.bookData_tab)
        self.verticalLayout_16.setObjectName(_fromUtf8("verticalLayout_16"))
        spacerItem10 = QtGui.QSpacerItem(607, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_16.addItem(spacerItem10)
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.verticalLayout_12 = QtGui.QVBoxLayout()
        self.verticalLayout_12.setObjectName(_fromUtf8("verticalLayout_12"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label_3 = QtGui.QLabel(self.bookData_tab)
        self.label_3.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_3.setTextFormat(QtCore.Qt.AutoText)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setMargin(5)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_2.addWidget(self.label_3)
        spacerItem11 = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem11)
        self.verticalLayout_12.addLayout(self.verticalLayout_2)
        self.verticalLayout_9 = QtGui.QVBoxLayout()
        self.verticalLayout_9.setObjectName(_fromUtf8("verticalLayout_9"))
        spacerItem12 = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_9.addItem(spacerItem12)
        self.label = QtGui.QLabel(self.bookData_tab)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setMargin(5)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_9.addWidget(self.label)
        spacerItem13 = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_9.addItem(spacerItem13)
        self.verticalLayout_12.addLayout(self.verticalLayout_9)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label_2 = QtGui.QLabel(self.bookData_tab)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setMargin(5)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_3.addWidget(self.label_2)
        self.verticalLayout_12.addLayout(self.verticalLayout_3)
        self.horizontalLayout_11.addLayout(self.verticalLayout_12)
        self.verticalLayout_15 = QtGui.QVBoxLayout()
        self.verticalLayout_15.setObjectName(_fromUtf8("verticalLayout_15"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.cmsCourse_edit = QtGui.QLineEdit(self.bookData_tab)
        self.cmsCourse_edit.setFrame(True)
        self.cmsCourse_edit.setObjectName(_fromUtf8("cmsCourse_edit"))
        self.horizontalLayout_10.addWidget(self.cmsCourse_edit)
        self.search_button = QtGui.QPushButton(self.bookData_tab)
        self.search_button.setObjectName(_fromUtf8("search_button"))
        self.horizontalLayout_10.addWidget(self.search_button)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        self.searchResults_combo = QtGui.QComboBox(self.bookData_tab)
        self.searchResults_combo.setObjectName(_fromUtf8("searchResults_combo"))
        self.verticalLayout.addWidget(self.searchResults_combo)
        self.verticalLayout_15.addLayout(self.verticalLayout)
        spacerItem14 = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_15.addItem(spacerItem14)
        self.verticalLayout_14 = QtGui.QVBoxLayout()
        self.verticalLayout_14.setObjectName(_fromUtf8("verticalLayout_14"))
        self.first_page_group = QtGui.QGroupBox(self.bookData_tab)
        self.first_page_group.setStyleSheet(_fromUtf8("border:0"))
        self.first_page_group.setTitle(_fromUtf8(""))
        self.first_page_group.setFlat(True)
        self.first_page_group.setCheckable(False)
        self.first_page_group.setObjectName(_fromUtf8("first_page_group"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.first_page_group)
        self.horizontalLayout_5.setContentsMargins(50, 0, 9, 10)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.leftPage_radio = QtGui.QRadioButton(self.first_page_group)
        self.leftPage_radio.setObjectName(_fromUtf8("leftPage_radio"))
        self.horizontalLayout_5.addWidget(self.leftPage_radio)
        self.rightPage_radio = QtGui.QRadioButton(self.first_page_group)
        self.rightPage_radio.setObjectName(_fromUtf8("rightPage_radio"))
        self.horizontalLayout_5.addWidget(self.rightPage_radio)
        self.verticalLayout_14.addWidget(self.first_page_group)
        spacerItem15 = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_14.addItem(spacerItem15)
        self.verticalLayout_15.addLayout(self.verticalLayout_14)
        self.verticalLayout_13 = QtGui.QVBoxLayout()
        self.verticalLayout_13.setObjectName(_fromUtf8("verticalLayout_13"))
        self.margins_group = QtGui.QGroupBox(self.bookData_tab)
        self.margins_group.setStyleSheet(_fromUtf8("border:0"))
        self.margins_group.setTitle(_fromUtf8(""))
        self.margins_group.setFlat(True)
        self.margins_group.setObjectName(_fromUtf8("margins_group"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.margins_group)
        self.horizontalLayout_4.setContentsMargins(50, 0, -1, 4)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.one_margin = QtGui.QRadioButton(self.margins_group)
        self.one_margin.setObjectName(_fromUtf8("one_margin"))
        self.horizontalLayout_4.addWidget(self.one_margin)
        self.two_margins = QtGui.QRadioButton(self.margins_group)
        self.two_margins.setObjectName(_fromUtf8("two_margins"))
        self.horizontalLayout_4.addWidget(self.two_margins)
        self.verticalLayout_13.addWidget(self.margins_group)
        self.verticalLayout_15.addLayout(self.verticalLayout_13)
        self.horizontalLayout_11.addLayout(self.verticalLayout_15)
        self.verticalLayout_16.addLayout(self.horizontalLayout_11)
        spacerItem16 = QtGui.QSpacerItem(607, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_16.addItem(spacerItem16)
        spacerItem17 = QtGui.QSpacerItem(607, 30, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_16.addItem(spacerItem17)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.label_6 = QtGui.QLabel(self.bookData_tab)
        self.label_6.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_6.setTextFormat(QtCore.Qt.AutoText)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.verticalLayout_4.addWidget(self.label_6)
        self.label_7 = QtGui.QLabel(self.bookData_tab)
        self.label_7.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_7.setTextFormat(QtCore.Qt.AutoText)
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.verticalLayout_4.addWidget(self.label_7)
        self.label_8 = QtGui.QLabel(self.bookData_tab)
        self.label_8.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_8.setTextFormat(QtCore.Qt.AutoText)
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.verticalLayout_4.addWidget(self.label_8)
        self.horizontalLayout_6.addLayout(self.verticalLayout_4)
        self.verticalLayout_8 = QtGui.QVBoxLayout()
        self.verticalLayout_8.setObjectName(_fromUtf8("verticalLayout_8"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.startZones_edit = QtGui.QLineEdit(self.bookData_tab)
        self.startZones_edit.setAcceptDrops(False)
        self.startZones_edit.setReadOnly(True)
        self.startZones_edit.setObjectName(_fromUtf8("startZones_edit"))
        self.horizontalLayout.addWidget(self.startZones_edit)
        self.addStart_button = QtGui.QPushButton(self.bookData_tab)
        self.addStart_button.setObjectName(_fromUtf8("addStart_button"))
        self.horizontalLayout.addWidget(self.addStart_button)
        self.verticalLayout_8.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.endZones_edit = QtGui.QLineEdit(self.bookData_tab)
        self.endZones_edit.setAcceptDrops(False)
        self.endZones_edit.setReadOnly(True)
        self.endZones_edit.setObjectName(_fromUtf8("endZones_edit"))
        self.horizontalLayout_2.addWidget(self.endZones_edit)
        self.addEnd_button = QtGui.QPushButton(self.bookData_tab)
        self.addEnd_button.setObjectName(_fromUtf8("addEnd_button"))
        self.horizontalLayout_2.addWidget(self.addEnd_button)
        self.verticalLayout_8.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.passthroughZones_edit = QtGui.QLineEdit(self.bookData_tab)
        self.passthroughZones_edit.setAcceptDrops(False)
        self.passthroughZones_edit.setReadOnly(True)
        self.passthroughZones_edit.setObjectName(_fromUtf8("passthroughZones_edit"))
        self.horizontalLayout_3.addWidget(self.passthroughZones_edit)
        self.addPassthrough_button = QtGui.QPushButton(self.bookData_tab)
        self.addPassthrough_button.setObjectName(_fromUtf8("addPassthrough_button"))
        self.horizontalLayout_3.addWidget(self.addPassthrough_button)
        self.verticalLayout_8.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_6.addLayout(self.verticalLayout_8)
        self.verticalLayout_16.addLayout(self.horizontalLayout_6)
        spacerItem18 = QtGui.QSpacerItem(607, 13, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_16.addItem(spacerItem18)
        self.settings_tabs.addTab(self.bookData_tab, _fromUtf8(""))
        self.verticalLayout_10.addWidget(self.settings_tabs)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_10.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.settings_tabs.setCurrentIndex(1)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label_4.setText(_translate("Dialog", "Логин", None))
        self.label_5.setText(_translate("Dialog", "Пароль", None))
        self.incorrectData_label.setText(_translate("Dialog", "Проверьте правильность логина и пароля", None))
        self.settings_tabs.setTabText(self.settings_tabs.indexOf(self.userData_tab), _translate("Dialog", "Настройки пользователя", None))
        self.label_3.setText(_translate("Dialog", "Курс в CMS", None))
        self.label.setText(_translate("Dialog", "Первая страница", None))
        self.label_2.setText(_translate("Dialog", "Поля", None))
        self.search_button.setText(_translate("Dialog", "Найти", None))
        self.leftPage_radio.setText(_translate("Dialog", "левая", None))
        self.rightPage_radio.setText(_translate("Dialog", "правая", None))
        self.one_margin.setText(_translate("Dialog", "с одной стороны", None))
        self.two_margins.setText(_translate("Dialog", "с обеих сторон", None))
        self.label_6.setText(_translate("Dialog", "Автозоны, начало параграфа", None))
        self.label_7.setText(_translate("Dialog", "Автозоны, конец параграфа", None))
        self.label_8.setText(_translate("Dialog", "Сквозные автозоны", None))
        self.addStart_button.setText(_translate("Dialog", "+", None))
        self.addEnd_button.setText(_translate("Dialog", "+", None))
        self.addPassthrough_button.setText(_translate("Dialog", "+", None))
        self.settings_tabs.setTabText(self.settings_tabs.indexOf(self.bookData_tab), _translate("Dialog", "Настройки учебника", None))

