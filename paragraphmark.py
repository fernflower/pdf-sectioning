#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from zonetypes import ZONE_ICONS


class QMark(QtGui.QWidget):
    WIDTH = 5
    SELECT_DELTA = 12
    SELECT_COLOUR = QtGui.QColor(0, 0, 0, 32)
    DESELECT_COLOUR = QtGui.QColor(180, 180, 180, 32)

    def __init__(self, pos, parent, name, delete_func, corrections):
        super(QMark, self).__init__(parent)
        self.corrections = corrections
        self.corrected = False
        self.is_selected = False
        self.cursor = QtGui.QCursor(QtCore.Qt.SizeAllCursor)
        self.delete_func = delete_func
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, parent)
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(pos.x(), pos.y()),
                                           QtCore.QSize(parent.width(),
                                                        self.WIDTH)))
        self.name = name
        self.label = QtGui.QLabel(self.name, parent)
        self._adjust_to_mark()
        self.update()

    # here corrections is a tuple
    #(l - left x-offset, that should be added to x,
    # r - right offset, added to width)
    def _apply_corrections(self, corrections):
        if not corrections:
            return
        left, right = corrections
        g = self.geometry()
        self.set_geometry(QtCore.QRect(g.x() + left, g.y(),
                                       g.width() + right, g.height()))

    def hide(self):
        # hide marks, and restore all corrections -> marks are stored as they
        # are, in pdf-coordinates
        self.mark.hide()
        self.label.hide()
        (l, r) = self.corrections
        if self.corrected:
            self._apply_corrections((-l, -r))
        self.corrected = False

    def show(self):
        if not self.corrected:
            self._apply_corrections(self.corrections)
            self.corrected = True
        self.mark.show()
        self.label.show()

    def geometry(self):
        return self.mark.geometry()

    def set_geometry(self, rect):
        self.mark.setGeometry(rect)
        self._adjust_to_mark()
        self.update()

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
        self.label.setGeometry(self.mark.x(),
                               self.mark.y(),
                               self.label.width(),
                               self.label.height())
        self.label.adjustSize()


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
        return self.geometry().y()

    def pos(self):
        return self.mark.pos()

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
    LABELS = {"start": u"Начало",
              "end": u"Конец"}

    def __init__(self, pos, parent, cas_id, name, page, delete_func, type,
                 corrections):
        super(QParagraphMark, self).__init__(QtCore.QPoint(0, pos.y()),
                                             parent,
                                             name, delete_func, corrections)
        self.cas_id = cas_id
        self.page = page
        self.ruler = None
        self.type = type
        self.label.setText(u"%s    %s" % (self.LABELS.get(self.type, u""),
                                          self.name))
        self._adjust_to_mark()

    def bind_to_ruler(self, ruler):
        self.ruler = ruler
        self.ruler.set_mark_geometry(self)

    def unbind_from_ruler(self):
        self.ruler = None


class QRulerMark(QMark):
    # TODO try to move to stylesheets
    SELECT_COLOUR = QtGui.QColor(200, 0, 0, 50)
    DESELECT_COLOUR = QtGui.QColor(100, 0, 0, 50)
    ORIENT_HORIZONTAL = "horizontal"
    ORIENT_VERTICAL = "vertical"

    def __init__(self, pos, parent, name, delete_func, orientation,
                 corrections):
        super(QRulerMark, self).__init__(pos, parent, name, delete_func,
                                         corrections)
        self.type = orientation
        # label is not needed, so have to overload all methods using it,
        # escpecialling those which do repainting
        self.label.hide()
        self.show()

    def show(self):
        super(QRulerMark, self).show()
        self.mark.show()
        self.label.hide()

    def set_mark_geometry(self, mark):
        mark.set_geometry(self.geometry())

    def update(self):
        self.mark.update()
        self.label.hide()

    def paint_me(self, painter):
        if self.is_selected:
            painter.fillRect(self.mark.geometry(), self.SELECT_COLOUR)
        else:
            painter.fillRect(self.mark.geometry(), self.DESELECT_COLOUR)


class QHorizontalRuler(QRulerMark):
    def __init__(self, pos, parent, name, delete_func, corrections):
        pos = QtCore.QPoint(0, pos.y())
        super(QRulerMark, self).__init__(pos, parent, name, delete_func,
                                         corrections)


class QVerticalRuler(QRulerMark):
    def __init__(self, pos, parent, name, delete_func, corrections):
        pos = QtCore.QPoint(pos.x(), 0)
        super(QRulerMark, self).__init__(pos, parent, name, delete_func,
                                         corrections)
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

    def set_mark_geometry(self, mark):
        g = self.geometry()
        m = mark.geometry()
        mark.set_geometry(QtCore.QRect(g.x(), m.y(), m.width(), m.height()))


class QStartParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, page, delete_func,
                 corrections=(0, 0)):
        super(QStartParagraph, self).__init__(pos,
                                              parent,
                                              cas_id,
                                              name,
                                              page,
                                              delete_func,
                                              "start",
                                              corrections)
        self.show()

class QEndParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, page, delete_func,
                 corrections=(0, 0)):
        super(QEndParagraph, self).__init__(pos,
                                            parent,
                                            cas_id,
                                            name,
                                            page,
                                            delete_func,
                                            "end",
                                            corrections)
        self.show()

MARKS_DICT = {"start": QStartParagraph,
              "end": QEndParagraph,
              QRulerMark.ORIENT_HORIZONTAL: QHorizontalRuler,
              QRulerMark.ORIENT_VERTICAL: QVerticalRuler}

def make_paragraph_mark(pos, parent, cas_id, name, page, delete_func, type,
                        corrections=(0, 0)):
    return MARKS_DICT[type](pos, parent, cas_id, name, page, delete_func,
                            corrections)

def make_ruler_mark(pos, parent, name, delete_func, orientation,
                    corrections=(0, 0)):
    return MARKS_DICT[orientation](pos, parent, name, delete_func, corrections)


class QZoneMark(QParagraphMark):
    def __init__(self, pos, parent, lesson_id, zone_id, page,
                 delete_func, type, objects, number, rubric, margin,
                 corrections=(0, 0), auto=False, pass_through=False):
        super(QZoneMark, self).__init__(pos, parent, lesson_id, zone_id, page,
                                        delete_func, type, corrections)
        self.auto = auto
        self.type = "single"
        self.pass_through = pass_through
        self.margin = margin
        self.rubric = rubric
        # just a list of dicts [ {oid, block-id, rubric} ]
        self.objects = objects
        self.number = number
        self.zone_id = zone_id
        self.icon_width = ZONE_ICONS[self.rubric].width()
        self.icon_height = ZONE_ICONS[self.rubric].height()
        # destroy unnecessary rubberband
        mark_pos = self.mark.pos()
        self.mark.hide()
        self.mark.setParent(None)
        self.mark = QtGui.QLabel(zone_id, parent)
        self.mark.setPixmap(QtGui.QPixmap.fromImage(ZONE_ICONS[self.rubric]))
        geometry = QtCore.QRect(mark_pos.x(), mark_pos.y(), self.icon_width,
                                self.icon_height)
        self.mark.setGeometry(geometry)
        self.mark.show()

    def show(self):
        super(QZoneMark, self).show()
        self.mark.show()
        self.label.hide()

    def should_show(self, page):
        return page == self.page

    def paint_me(self, painter):
        if self.is_selected:
            painter.fillRect(self.mark.geometry(), self.SELECT_COLOUR)
        else:
            painter.fillRect(self.mark.geometry(), self.DESELECT_COLOUR)

    def set_page(self, page):
        pass


class QPassThroughZoneMark(QZoneMark):
    def __init__(self, pos, parent, lesson_id, zone_id, page,
                 delete_func, type, objects, number, rubric, margin,
                 corrections=(0, 0), pages=None):
        super(QPassThroughZoneMark, self).__init__(pos, parent,
                                               lesson_id, zone_id,
                                               page,
                                               delete_func,
                                               type, objects, number, rubric,
                                               margin, corrections, True, True)
        self.type = "repeat"
        self.pages = {page: pos.y()}
        if pages:
            for p, y in pages.items():
                if p not in self.pages.keys():
                    self.pages[p] = y

    def should_show(self, page):
        return page in self.pages.keys()

    def show(self):
        super(QPassThroughZoneMark, self).show()
        if not self.should_show(self.page):
            return
        g = self.geometry()
        self.set_geometry(QtCore.QRect(g.x(),
                                       self.pages[self.page], g.width(),
                                       g.height()))

    def move(self, delta):
        super(QPassThroughZoneMark, self).move(delta)
        g = self.geometry()
        self.pages[self.page] = g.y()
        print self.pages

    def set_page(self, page):
        if self.should_show(page):
            self.page = page

    def remove_page(self, page):
        if self.should_show(page):
            del self.pages[page]

    def can_be_removed(self):
        return self.pages == {}
