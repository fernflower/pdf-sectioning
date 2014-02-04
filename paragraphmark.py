#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class QMark(QtGui.QWidget):
    WIDTH = 5
    SELECT_DELTA = 12
    SELECT_COLOUR = QtGui.QColor(0, 0, 0, 32)
    DESELECT_COLOUR = QtGui.QColor(180, 180, 180, 32)

    def __init__(self, pos, parent, name, delete_func):
        super(QMark, self).__init__(parent)
        self.is_selected = False
        self.delete_func = delete_func
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, parent)
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(pos.x(), pos.y()),
                                           QtCore.QSize(parent.width(),
                                                        self.WIDTH)))
        self.mark.show()
        self.name = name
        self.label = QtGui.QLabel(self.name, parent)
        self._adjust_to_mark()
        self.label.show()
        # repaint newly created as unselected
        self.update()

    def hide(self):
        self.mark.hide()
        self.label.hide()

    def show(self):
        self.mark.show()
        self.label.show()

    def geometry(self):
        return self.mark.geometry()

    def set_geometry(self, rect):
        self.mark.setGeometry(rect)
        self._adjust_to_mark()

    def paint_me(self, painter):
        if self.is_selected:
            painter.fillRect(self.mark.geometry(), self.SELECT_COLOUR)
            painter.fillRect(self.label.geometry(), self.SELECT_COLOUR)
        else:
            painter.fillRect(self.mark.geometry(), self.DESELECT_COLOUR)
            painter.fillRect(self.label.geometry(), self.DESELECT_COLOUR)

    def toggle_selected(self):
        self.is_selected = not self.is_selected
        self.update()

    def set_selected(self, value):
        self.is_selected = value
        self.update()

    def destroy(self):
        self.hide()
        self.mark.setParent(None)
        self.label.setParent(None)
        self.mark.deleteLater()
        self.label.deleteLater()

    def _adjust_to_mark(self):
        self.label.adjustSize()
        self.label.setGeometry(self.mark.x(),
                               self.mark.y(),
                               self.label.width(),
                               self.label.height())


    def adjust(self, scale):
        rect = self.geometry()
        self.mark.setGeometry(rect.x() * scale,
                              rect.y() * scale,
                              rect.width() * scale,
                              rect.height())
        self._adjust_to_mark()

    def select(self, value):
        self.is_selected = value

    # get start-y coordinate
    def y(self):
        return self.mark.pos().y()

    def update(self):
        self.mark.update()
        self.label.update()

    def contains(self, cursor):
        return self.geometry().contains(cursor)

    def intersects(self, rect):
        return self.geometry().intersects(rect)

    def move(self, delta):
        g = self.mark.geometry()
        self.mark.setGeometry(g.x(),
                              g.y() + delta.y(),
                              g.width(),
                              g.height())
        self._adjust_to_mark()

    def delete(self):
        self.delete_func(self)

class QParagraphMark(QMark):
    def __init__(self,
                 pos, parent, cas_id, name, toc_num, page, delete_func, type):
        super(QParagraphMark, self).__init__(QtCore.QPoint(0, pos.y()),
                                             parent,
                                             name, delete_func)
        self.cas_id = cas_id
        self.page = page
        self.toc_num = toc_num
        self.ruler = None
        self.type = type
        self.label.setText("%s of paragraph %s" % (self.type, self.name))

    def bind_to_ruler(self, ruler):
        self.ruler = ruler
        self.set_geometry(self.ruler.geometry())

    def unbind_from_ruler(self):
        self.ruler = None

    def geometry(self):
        # if ruler is present, then take one of the coordinates (x or y,
        # depending on ruler) from ruler. Otherwise use super().geometry()
        if self.ruler:
            return self.ruler.recalc_geometry(self)
        else:
            return super(QParagraphMark, self).geometry()


class QRulerMark(QMark):
    SELECT_COLOUR = QtGui.QColor(200, 0, 0, 50)
    DESELECT_COLOUR = QtGui.QColor(100, 0, 0, 50)
    ORIENT_HORIZONTAL = "horizontal"
    ORIENT_VERTICAL = "vertical"

    def __init__(self, pos, parent, name, delete_func, orientation):
        self.type = orientation

    def recalc_geometry(self, mark):
        # regardless of mark by default
        return self.geometry()


class QHorizontalRuler(QRulerMark):
    def __init__(self, pos, parent, name, delete_func):
        pos = QtCore.QPoint(0, pos.y())
        super(QRulerMark, self).__init__(pos, parent, name, delete_func)


class QVerticalRuler(QRulerMark):
    def __init__(self, pos, parent, name, delete_func):
        pos = QtCore.QPoint(pos.x(), 0)
        super(QRulerMark, self).__init__(pos, parent, name, delete_func)
        vert_rect = QtCore.QRect(QtCore.QPoint(pos.x(), pos.y()),
                                 QtCore.QSize(QMark.WIDTH,
                                            parent.height()))
        self.set_geometry(vert_rect)

    def move(self, delta):
        g = self.mark.geometry()
        self.mark.setGeometry(g.x() + delta.x(),
                              g.y(),
                              g.width(),
                              g.height())
        self._adjust_to_mark()

    def adjust(self, scale):
        rect = self.geometry()
        self.mark.setGeometry(rect.x() * scale,
                              rect.y() * scale,
                              rect.width(),
                              rect.height() * scale)
        self._adjust_to_mark()

    def recalc_geometry(self, mark):
        # y coordinate if taken from mark, x - from ruler
        return QtCore.QRect(self.geometry.x(), mark.geometry().x(),
                            self.geometry().width(), self.geometry().height())


class QStartParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, toc_num, page, delete_func):
        super(QStartParagraph, self).__init__(pos,
                                              parent,
                                              cas_id,
                                              name,
                                              toc_num,
                                              page,
                                              delete_func,
                                              "start")

class QEndParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, toc_num, page, delete_func):
        super(QEndParagraph, self).__init__(pos,
                                            parent,
                                            cas_id,
                                            name,
                                            toc_num,
                                            page,
                                            delete_func,
                                            "end")

MARKS_DICT = {"start": QStartParagraph,
              "end": QEndParagraph,
              QRulerMark.ORIENT_HORIZONTAL: QHorizontalRuler,
              QRulerMark.ORIENT_VERTICAL: QVerticalRuler}

def make_paragraph_mark(pos, parent, cas_id, name, toc_num, page, delete_func,
                        type):
    return MARKS_DICT[type](pos, parent, cas_id, name, toc_num, page, delete_func)

def make_ruler_mark(pos, parent, name, delete_func, orientation):
    return MARKS_DICT[orientation](pos, parent, name, delete_func)
