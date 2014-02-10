#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from paragraphmark import QStartParagraph, QEndParagraph, QParagraphMark, \
    QRulerMark, make_paragraph_mark, make_ruler_mark
from timelogger import TimeLogger

tlogger = TimeLogger()

# this class manages all keys/mouse clicks and calls actions from page_viewer
# class. It keeps track of all paragraph marks with coordinates in dict, key is
# cas-id
class QImageLabel(QtGui.QLabel):
    STYLESHEET = "QImageLabel { background-color: rgb(58, 56, 56); }"
    MOVE_KEYS_DELTA = { QtCore.Qt.Key_Up: QtCore.QPoint(0, -2),
                        QtCore.Qt.Key_Down: QtCore.QPoint(0, 2),
                        QtCore.Qt.Key_Left: QtCore.QPoint(-2, 0),
                        QtCore.Qt.Key_Right: QtCore.QPoint(2, 0) }

    def __init__(self, parent, controller):
        self.controller = controller
        # keep it here on order to pass some keyPressEvents to parent
        self.parent = parent
        self.last_selected = None
        # for move event, to calculate delta
        # TODO there might be another way, perhaps to retrieve delta from move event
        self.coordinates = None
        super(QImageLabel, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet(self.STYLESHEET)

    def wheelEvent(self, event):
        self.controller.zoom(event.delta())

    # override paint event
    def paintEvent(self, event):
        super(QImageLabel, self).paintEvent(event)
        img = self.controller.get_image()
        pixmap = QtGui.QPixmap.fromImage(img)
        painter = QtGui.QPainter(self)
        marks_and_rulers = self.controller.get_current_page_marks() + \
                           self.controller.get_rulers()
        for mark in marks_and_rulers:
            mark.paint_me(painter)
            mark.update()
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        # update all necessary data in parent (bookviewer)
        self.parent.update()

    def mousePressEvent(self, event):
        # general for both modes
            # if clicked on already existing mark -> select it, deselecting
            # anything that has been selected earlier
            # if clicked with shift -> add to existing selection
        def process_selected(selected):
            modifiers = QtGui.QApplication.keyboardModifiers()
            if modifiers != QtCore.Qt.ShiftModifier:
                if not self.last_selected == selected:
                    selected.toggle_selected()
                self.controller.deselect_all([selected])
            else:
                # for group selection second click removes object from group
                # selection
                selected.toggle_selected()
            self.last_selected = selected

        # disable right mouse click as it shows context menu
        if event.buttons() == QtCore.Qt.RightButton:
            return super(QImageLabel, self).mousePressEvent(event)
        if event.buttons() == QtCore.Qt.LeftButton:
            selected = self.controller.find_any_at_point(event.pos())
            self.coordinates = event.pos()
            if selected:
                process_selected(selected)
            else:
                # deselected everything selected earlier on page
                self.controller.deselect_all()
                self.controller._create_mark_on_click(event.pos(), self)
        self.update()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.pos().x() - self.coordinates.x(),
                              event.pos().y() - self.coordinates.y())
        self.coordinates = event.pos()
        self.controller.move(delta, self.coordinates)
        self.update()

    def keyPressEvent(self, event):
        if self.controller.selected_marks_and_rulers() != [] and \
                event.key() in self.MOVE_KEYS_DELTA.keys():
            delta = self.MOVE_KEYS_DELTA[event.key()]
            self.coordinates = self.coordinates + delta
            self.controller.move(delta, self.coordinates)
        else:
            # should be here to navigate when focused
            self.parent.keyPressEvent(event)
        self.update()
