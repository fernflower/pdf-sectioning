# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout.ui'
#
# Created: Thu Mar 20 19:25:15 2014
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
        MainWindow.resize(675, 435)
        MainWindow.setFocusPolicy(QtCore.Qt.NoFocus)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.scrollArea = QtGui.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(9, 9, 16, 16))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 16, 16))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(341, 9, 278, 245))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.verticalLayout = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.listView = QtGui.QListView(self.tab)
        self.listView.setObjectName(_fromUtf8("listView"))
        self.verticalLayout.addWidget(self.listView)
        self.consoleLayout = QtGui.QHBoxLayout()
        self.consoleLayout.setObjectName(_fromUtf8("consoleLayout"))
        self.verticalLayout.addLayout(self.consoleLayout)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.tab_2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.treeView = QtGui.QTreeView(self.tab_2)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.horizontalLayout.addWidget(self.treeView)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 675, 20))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuTools = QtGui.QMenu(self.menubar)
        self.menuTools.setObjectName(_fromUtf8("menuTools"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(True)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionLoad_pdf = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("buttons/button_wafer.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLoad_pdf.setIcon(icon)
        self.actionLoad_pdf.setMenuRole(QtGui.QAction.NoRole)
        self.actionLoad_pdf.setObjectName(_fromUtf8("actionLoad_pdf"))
        self.actionSmartSave = QtGui.QAction(MainWindow)
        self.actionSmartSave.setIcon(icon)
        self.actionSmartSave.setObjectName(_fromUtf8("actionSmartSave"))
        self.actionLoad_markup = QtGui.QAction(MainWindow)
        self.actionLoad_markup.setIcon(icon)
        self.actionLoad_markup.setObjectName(_fromUtf8("actionLoad_markup"))
        self.actionSetHorizontalRuler = QtGui.QAction(MainWindow)
        self.actionSetHorizontalRuler.setIcon(icon)
        self.actionSetHorizontalRuler.setObjectName(_fromUtf8("actionSetHorizontalRuler"))
        self.actionSetVerticalRuler = QtGui.QAction(MainWindow)
        self.actionSetVerticalRuler.setIcon(icon)
        self.actionSetVerticalRuler.setObjectName(_fromUtf8("actionSetVerticalRuler"))
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionLoad_pdf)
        self.toolBar.addAction(self.actionLoad_markup)
        self.toolBar.addAction(self.actionSmartSave)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSetHorizontalRuler)
        self.toolBar.addAction(self.actionSetVerticalRuler)
        self.toolBar.addSeparator()

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Структура", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Разметка", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit", None))
        self.menuTools.setTitle(_translate("MainWindow", "Tools", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.actionLoad_pdf.setText(_translate("MainWindow", "Загрузить pdf", None))
        self.actionLoad_pdf.setIconText(_translate("MainWindow", "Загрузить pdf", None))
        self.actionLoad_pdf.setToolTip(_translate("MainWindow", "Загрузить pdf", None))
        self.actionSmartSave.setText(_translate("MainWindow", "Сохранить как ...", None))
        self.actionLoad_markup.setText(_translate("MainWindow", "Загрузить разметку", None))
        self.actionSetHorizontalRuler.setText(_translate("MainWindow", "Установить горизонтальный разделитель", None))
        self.actionSetHorizontalRuler.setIconText(_translate("MainWindow", "Установить горизонтальный разделитель", None))
        self.actionSetVerticalRuler.setText(_translate("MainWindow", "Установить вертикальный разделитель", None))
        self.actionSetVerticalRuler.setIconText(_translate("MainWindow", "Установить вертикальный разделитель", None))

