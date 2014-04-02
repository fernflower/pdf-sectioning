#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class QMark(QtGui.QWidget):
    WIDTH = 5
    SELECT_COLOUR = QtGui.QColor(0, 0, 0, 32)
    DESELECT_COLOUR = QtGui.QColor(180, 180, 180, 32)

    # pos in a tuple (x, y)
    def __init__(self, pos, parent, name, delete_func, corrections):
        super(QMark, self).__init__(parent)
        self.parent = parent
        self.corrections = corrections
        self.corrected = False
        self.is_selected = False
        self.cursor = QtGui.QCursor(QtCore.Qt.SizeAllCursor)
        self.delete_func = delete_func
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, parent)
        (pos_x, pos_y) = pos
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(pos_x, pos_y),
                                           QtCore.QSize(parent.width(),
                                                        self.WIDTH)))
        self.name = name
        self.label = QtGui.QLabel(self.name, parent)
        self._adjust_to_mark()
        self.update()

    def is_paragraph(self):
        return isinstance(self, QParagraphMark)

    def is_start(self):
        return isinstance(self, QStartParagraph)

    def is_end(self):
        return isinstance(self, QEndParagraph)

    def is_ruler(self):
        return isinstance(self, QRulerMark)

    def is_zone(self):
        return isinstance(self, QZoneMark)

    def is_passthrough_zone(self):
        return isinstance(self, QPassThroughZoneMark)

    def is_inner_zone(self):
        return isinstance(self, QInnerZoneMark)

    def change_corrections(self, new_corrections, curr_page):
        pass

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

    def geometry_as_tuple(self):
        g = self.geometry()
        return (g.x(), g.y(), g.width(), g.height())

    def pos_as_tuple(self):
        return (self.pos().x(), self.pos().y())

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

    def y(self):
        return self.geometry().y()

    def x(self):
        return self.geometry().x()

    def pos(self):
        return self.mark.pos()

    def update(self):
        self.mark.update()
        self.label.update()

    def contains(self, point_tuple):
        x, y = point_tuple
        point = QtCore.QPoint(x, y)
        return self.geometry().contains(point)

    def intersects(self, rect_tuple):
        x1, y1, x2, y2 = rect_tuple
        rect = QtCore.QRect(QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))
        return self.geometry().intersects(rect)

    def _calc_move(self, (delta_x, delta_y)):
        x, y, w, h = self.geometry_as_tuple()
        return (x, y + delta_y, w, h)

    # here delta is a tuple (x, y)
    def move(self, delta):
        x, y, w, h = self._calc_move(delta)
        self.mark.setGeometry(x, y, w, h)
        self._adjust_to_mark()

    def delete(self):
        self.delete_func(self)

class QParagraphMark(QMark):
    LABELS = {"start": u"Начало",
              "end": u"Конец"}

    def __init__(self, pos, parent, cas_id, name, page, delete_func, type,
                 corrections):
        (pos_x, pos_y) = pos
        super(QParagraphMark, self).__init__((0, pos_y), parent, name,
                                             delete_func, corrections)
        self.cas_id = cas_id
        # page this moment has to be shown at (can be modified if the same
        # objects has to appear on one page but in various locations)
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

    def __init__(self, pos, parent, name, delete_func, type,
                 corrections):
        super(QRulerMark, self).__init__(pos, parent, name, delete_func,
                                         corrections)
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
    def __init__(self, pos, parent, delete_func, corrections, name=""):
        (pos_x, pos_y) = pos
        super(QRulerMark, self).__init__((0, pos_y), parent, name,
                                         delete_func, corrections)


class QVerticalRuler(QRulerMark):
    def __init__(self, pos, parent, delete_func, corrections, name=""):
        (pos_x, pos_y) = pos
        super(QRulerMark, self).__init__((pos_x, 0), parent, name,
                                         delete_func, corrections)
        vert_rect = QtCore.QRect(QtCore.QPoint(pos_x, 0),
                                 QtCore.QSize(QMark.WIDTH,
                                            parent.height()))
        self.set_geometry(vert_rect)

    def _calc_move(self, (delta_x, delta_y)):
        x, y, w, h = self.geometry_as_tuple()
        return (x + delta_x, y, w, h)

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

def make_ruler_mark(pos, parent, delete_func, type,
                    corrections=(0, 0), name=u""):
    return MARKS_DICT[type](pos=pos, parent=parent, name=name,
                            delete_func=delete_func, corrections=corrections)

def make_zone_mark(pos, parent, cas_id, zone_id, page,
                   delete_func, objects, rubric, margin, icon,
                   corrections=(0, 0), inner=False, auto=False,
                   pass_through=False, pages=None, number="00",
                   recalc_corrections=None):
    if not pass_through:
        return QZoneMark(pos, parent, cas_id, zone_id, page,
                         delete_func, objects, rubric, margin,
                         number, icon, corrections, auto)
    elif inner:
        return QInnerZoneMark(pos, parent, cas_id, zone_id, page,
                              delete_func, objects, rubric, icon, pages)
    return QPassThroughZoneMark(pos, parent, cas_id, zone_id, page,
                                delete_func, objects, rubric,
                                margin, icon, corrections, pages,
                                recalc_corrections)

# TODO reconsider this, there might be another way of testing bookcontroller
class MarkCreator(object):
    def make_paragraph_mark(self, *args, **kwargs):
        return make_paragraph_mark(*args, **kwargs)

    def make_ruler_mark(self, *args, **kwargs):
        return make_ruler_mark(*args, **kwargs)

    def make_zone_mark(self, *args, **kwargs):
        return make_zone_mark(*args, **kwargs)


# here type means zone type stored in xml (single, repeat etc)
class QZoneMark(QParagraphMark):
    def __init__(self, pos, parent, cas_id, zone_id, page,
                 delete_func, objects, rubric, margin, number, icon,
                 corrections=(0, 0), auto=False, pass_through=False):
        super(QZoneMark, self).__init__(pos, parent, cas_id, zone_id, page,
                                        delete_func, "single", corrections)
        self.auto = auto
        self.type = "single"
        self.pass_through = pass_through
        self.margin = margin
        self.rubric = rubric
        # pages that zone should appear at
        (pos_x, pos_y) = pos
        self.pages = {page: pos_y}
        # just a list of dicts [ {oid, block-id, rubric} ]
        self.objects = objects
        self.number = number
        self.zone_id = zone_id
        # destroy unnecessary rubberband
        mark_pos = self.mark.pos()
        self.mark.hide()
        self.mark.setParent(None)
        self.mark = QtGui.QLabel(zone_id, parent)
        self.mark.setPixmap(QtGui.QPixmap.fromImage(icon))
        geometry = QtCore.QRect(mark_pos.x(), mark_pos.y(), icon.width(),
                                icon.height())
        self.mark.setGeometry(geometry)
        self.mark.show()

    def change_corrections(self, new_corrections, page):
        # to make not corrected if corrected
        self.hide()
        self.corrections = new_corrections
        if self.should_show(page):
            self.show()

    def adjust(self, scale):
        rect = self.geometry()
        self.mark.setGeometry(rect.x() * scale,
                              rect.y() * scale,
                              rect.width(),
                              rect.height())
        self._adjust_to_mark()

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

    def to_dict(self):
        return {"n": self.number,
                "type": self.type,
                "page": self.page,
                "y": self.y(),
                "rubric": self.rubric,
                "objects": self.objects,
                "at": self.margin }

    def set_page(self, page):
        if self.should_show(page):
            self.page = page

    def remove_page(self, page):
        if self.should_show(page):
            del self.pages[page]

    def remove_pages(self):
        self.pages = {}

    def can_be_removed(self):
        return self.pages == {}

    def should_show(self, page):
        return page in self.pages.keys()


class QPassThroughZoneMark(QZoneMark):
    def __init__(self, pos, parent, cas_id, zone_id, page,
                 delete_func, objects, rubric, margin, icon,
                 corrections=(0, 0), pages=None, recalc_corrections=None):
        super(QPassThroughZoneMark, self).__init__(pos, parent,
                                                   cas_id, zone_id,
                                                   page,
                                                   delete_func,
                                                   objects,
                                                   rubric, margin, "00", icon,
                                                   corrections, True, True)
        self.type = "repeat"
        (pos_x, pos_y) = pos
        self.initial_y = pos_y
        self.recalc_corrections = recalc_corrections
        if pages:
            for p, y in pages.items():
                if p not in self.pages.keys():
                    self.pages[p] = y

    def show(self):
        # update corrections (depending on page)
        if self.recalc_corrections:
            self.corrections = self.recalc_corrections(self.page, self.rubric)
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

    def to_dict(self):
        return {"n": self.number,
                "type": self.type,
                "placements": [{'page':p, 'y':y} for (p, y)
                               in self.pages.items()],
                "y": self.y(),
                "rubric": self.rubric,
                "objects": self.objects,
                "at": self.margin }


class QInnerZoneMark(QZoneMark):
    def __init__(self, pos, parent, cas_id, zone_id, page, delete_func,
                 objects, rubric, icon, pages=None):
        super(QInnerZoneMark, self).__init__(pos, parent, cas_id, zone_id,
                                             page, delete_func, objects,
                                             rubric, "", "00", icon,
                                             (0, 0), False, True)
        self.type = "inner"
        self.initial_pos = pos
        # pos is set by x and y
        self.set_geometry(QtCore.QRect(pos[0], pos[1],
                                       self.geometry().width(),
                                       self.geometry().height()))
        self.pages = {page: self.initial_pos}
        if pages:
            for p, pos in pages.items():
                if p not in self.pages.keys():
                    self.pages[p] = pos

    def show(self):
        super(QInnerZoneMark, self).show()
        if not self.should_show(self.page):
            return
        g = self.geometry()
        self.set_geometry(QtCore.QRect(self.pages[self.page][0],
                                       self.pages[self.page][1],
                                       g.width(), g.height()))
    def _calc_move(self, (delta_x, delta_y)):
        x, y, w, h = self.geometry_as_tuple()
        return (x + delta_x, y + delta_y, w, h)

    def move(self, delta):
        super(QInnerZoneMark, self).move(delta)
        g = self.geometry()
        self.pages[self.page] = (g.x(), g.y())

    def to_dict(self):
        return {"n": self.number,
                "type": self.type,
                "placements": [{'page':p, 'y':y} for (p, y)
                               in self.pages.items()],
                "x": self.x(),
                "y": self.y(),
                "rubric": self.rubric,
                "objects": self.objects,
                "at": self.margin }
