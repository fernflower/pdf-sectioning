#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


# this class manages all keys/mouse clicks and calls actions from page_viewer
# class. It keeps track of all paragraph marks with coordinates in dict, key is
# cas-id
class QImageLabel(QtGui.QLabel):
    STYLESHEET = "QImageLabel { background-color: rgb(58, 56, 56); }"
    MOVE_KEYS_DELTA = { QtCore.Qt.Key_Up: QtCore.QPoint(0, -2),
                        QtCore.Qt.Key_Down: QtCore.QPoint(0, 2),
                        QtCore.Qt.Key_Left: QtCore.QPoint(-2, 0),
                        QtCore.Qt.Key_Right: QtCore.QPoint(2, 0) }

    def __init__(self, parent, controller, toc_controller):
        self.controller = controller
        self.toc_controller = toc_controller
        # keep it here on order to pass some keyPressEvents to parent
        self.bookviewer = parent
        self.last_selected = None
        self.cursor_overridden = False
        # for move event, to calculate delta
        # TODO there might be another way, perhaps to retrieve delta from move event
        self.coordinates = None
        self.zoomed_signal = QtCore.SIGNAL("zoomChanged(float)")
        self.margin_color = QtGui.QColor(105, 105, 105)
        super(QImageLabel, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet(self.STYLESHEET)

    @property
    def coordinates_as_tuple(self):
        if self.coordinates:
            return (self.coordinates.x(), self.coordinates.y())

    def wheelEvent(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            scale = self.controller.zoom(event.delta())
            # notify parent that zoom has changed and combo box has to be
            # updated with new value
            self.emit(self.zoomed_signal, scale)
        else:
            self.bookviewer.call_wheelEvent(event)

    def _set_cursor(self, pos):
        # if over a ruler or mark - change cursor appropriately
        any_mark = self.controller.find_any_at_point((pos.x(), pos.y()))
        if any_mark:
            if not self.cursor_overridden:
                QtGui.QApplication.setOverrideCursor(
                    QtGui.QCursor(any_mark.cursor))
            self.cursor_overridden = True
        elif self.cursor_overridden:
            self.cursor_overridden = False
            QtGui.QApplication.restoreOverrideCursor()

    # override paint event
    def paintEvent(self, event):
        super(QImageLabel, self).paintEvent(event)
        img = self.controller.get_image()
        pixmap = None
        if img:
            if self.controller.is_markup_mode():
                # get margins info in order to add rects to image
                w = self.controller.margin_width
                m_width = w
                if self.controller.has_both_margins():
                    m_width = m_width + w
                resulting_pmp = QtGui.QPixmap(m_width + img.width(), img.height())
                pixmap_painter = QtGui.QPainter(resulting_pmp)
                pixmap_painter.setBrush(self.margin_color)
                pixmap_painter.setPen(self.margin_color)
                img_pmp = QtGui.QPixmap.fromImage(img)
                if self.controller.has_left_margin():
                    pixmap_painter.drawRect(0, 0, w, img.height())
                    pixmap_painter.drawPixmap(w, 0, img.width(), img.height(),
                                              img_pmp)
                else:
                    pixmap_painter.drawPixmap(0, 0, img.width(), img.height(),
                                              img_pmp)
                if self.controller.has_both_margins():
                    pixmap_painter.drawRect(w + img.width(), 0, w, img.height())
                elif self.controller.has_right_margin():
                    pixmap_painter.drawRect(img.width(), 0, w, img.height())
                pixmap_painter.end()
                pixmap = resulting_pmp
            else:
                pixmap = QtGui.QPixmap.fromImage(img)
            # update all necessary data in parent (bookviewer)
            self.setPixmap(pixmap)
            self.setFixedSize(pixmap.size())
            painter = QtGui.QPainter(self)
            marks_and_rulers = self.controller.get_current_page_marks() + \
                            self.controller.get_rulers()
            for mark in marks_and_rulers:
                mark.paint_me(painter)
                mark.update()
            self._set_cursor(self.mapFromGlobal(QtGui.QCursor.pos()))
        self.bookviewer.update()

    def mousePressEvent(self, event):
        # general for both modes
            # if clicked on already existing mark -> select it, deselecting
            # anything that has been selected earlier
            # if clicked with shift -> add to existing selection
        def process_selected(selected):
            if modifiers != QtCore.Qt.ShiftModifier:
                if self.last_selected != selected:
                    selected.toggle_selected()
                    self.controller.deselect_all([selected])
                    self.toc_controller.select_toc_for_mark(
                        selected, self.controller.operational_mode)
            else:
                # for group selection second click removes object from group
                # selection
                selected.toggle_selected()
                # select corr. toc_elem in a list
            self.last_selected = selected

        modifiers = QtGui.QApplication.keyboardModifiers()
        # select elem under right click and show menu
        if event.buttons() == QtCore.Qt.RightButton:
            any_mark = self.controller.find_any_at_point((event.pos().x(),
                                                          event.pos().y()))
            if any_mark and not any_mark.is_selected:
                self.controller.deselect_all()
                any_mark.toggle_selected()
            if any_mark:
                self.last_selected = any_mark
                return self.bookviewer.show_context_menu(self.mapToGlobal(
                    event.pos()))
        if event.buttons() == QtCore.Qt.LeftButton:
            selected = self.controller.find_any_at_point((event.pos().x(),
                                                          event.pos().y()))
            self.coordinates = event.pos()
            if selected:
                if modifiers == QtCore.Qt.AltModifier and selected.is_ruler():
                    # try to create new mark and bind it to ruler
                    self.controller.deselect_all()
                    mark = self.controller._create_mark_on_click(
                        self.coordinates_as_tuple, self)
                    mark.bind_to_ruler(selected)
                else:
                    process_selected(selected)
            else:
                # deselected everything selected earlier on page
                self.controller.deselect_all()
                self.controller._create_mark_on_click(
                    self.coordinates_as_tuple, self)
                self.last_selected = None
        self.update()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.pos().x() - self.coordinates.x(),
                              event.pos().y() - self.coordinates.y())
        self.coordinates = event.pos()
        self.controller.move((delta.x(), delta.y()), self.coordinates_as_tuple)
        self.update()

    def keyPressEvent(self, event):
        if self.controller.selected_marks_and_rulers != [] and \
                event.key() in self.MOVE_KEYS_DELTA.keys():
            delta = self.MOVE_KEYS_DELTA[event.key()]
            self.coordinates = self.coordinates + delta
            self.controller.move(delta, self.coordinates_as_tuple)
        self.update()
