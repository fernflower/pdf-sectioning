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
    MODE_NORMAL = "normal"
    MODE_RULER_HOR = QRulerMark.ORIENT_HORIZONTAL
    MODE_RULER_VERT = QRulerMark.ORIENT_VERTICAL

    def __init__(self, parent, page_viewer):
        self.page_viewer = page_viewer
        self.paragraph_marks = {}
        self.is_any_mark_selected = False
        self.rulers = []
        self.mode = QImageLabel.MODE_NORMAL
        # for move event, to calculate delta
        # TODO there might be another way, perhaps tp retrieve delta from move event
        self.coordinates = None
        super(QImageLabel, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def set_ruler_mode(self, mode):
        self.mode = mode

    def set_normal_mode(self):
        self.mode = QImageLabel.MODE_NORMAL

    @property
    def cursor_pos(self):
        return self.mapFromGlobal(QtGui.QCursor.pos())

    def get_selected_rulers(self):
        return [r for r in self.get_rulers() if r.is_selected]

    def is_ruler_mode(self):
        return self.mode == QImageLabel.MODE_RULER_HOR or \
            self.mode == QImageLabel.MODE_RULER_VERT

    def is_normal_mode(self):
        return self.mode == QImageLabel.MODE_NORMAL

    def get_rulers(self):
        #TODO return all rulers
        return self.rulers

    # return corresponding toc_elem for start\end paragraph mark
    def get_toc_elem(self, mark):
        return self.page_viewer.get_toc_elem(mark.cas_id)

    def wheelEvent(self, event):
        self.page_viewer.zoom(event.delta())
        self.update()

    # override paint event
    def paintEvent(self, event):
        super(QImageLabel, self).paintEvent(event)
        img = self.page_viewer.get_image()
        pixmap = QtGui.QPixmap.fromImage(img)
        painter = QtGui.QPainter(self)
        marks_and_rulers = self.page_viewer.get_current_page_marks() + \
                           self.get_rulers()
        for mark in marks_and_rulers:
            mark.paint_me(painter)
            mark.update()
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())

    # start\end paragraph marks creation
    def _create_mark_on_click(self, event):
        # else create new one if any TOC elem selected and free space for
        # start\end mark available
        if self.is_normal_mode() and self.page_viewer.is_toc_selected:
            toc_elem = self.page_viewer.get_selected_toc_elem()
            page = self.page_viewer.pageNum
            key = toc_elem.cas_id
            (start, end) = (None, None)
            mark_type = self.get_available_marks(key)
            if not mark_type:
                return
            mark = make_paragraph_mark(event.pos(),
                                    self,
                                    toc_elem.cas_id,
                                    toc_elem.name,
                                    toc_elem.order_num,
                                    page,
                                    self.delete_mark,
                                    mark_type[0])
            self.add_mark(mark)
        elif self.is_ruler_mode():
            mark = make_ruler_mark(event.pos(),
                                   self,
                                   "i am a ruler",
                                   self.delete_ruler,
                                   self.mode)
            self.add_ruler(mark)
        self.update()

    def mousePressEvent(self, event):
        # general for both modes
            # if clicked on already existing mark -> select it, deselecting
            # anything that has been selected earlier
            # if clicked with shift -> add to existing selection
        def process_selected(selected):
            modifiers = QtGui.QApplication.keyboardModifiers()
            self.is_any_mark_selected = True
            selected.toggle_selected()
            if modifiers != QtCore.Qt.ShiftModifier:
                self.is_any_mark_selected = selected.is_selected
                map(lambda m: m.set_selected(False),
                    filter(lambda x: x!=selected,
                            self.page_viewer.selected_marks_and_rulers()))

        # disable right mouse click as it shows context menu
        if event.buttons() == QtCore.Qt.RightButton:
            return super(QImageLabel, self).mousePressEvent(event)
        if event.buttons() == QtCore.Qt.LeftButton:
            selected = self.find_any_at_point(self.mapToGlobal(event.pos()))
            self.coordinates = event.pos()
            if selected:
                process_selected(selected)
            else:
                self._create_mark_on_click(event)

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.pos().x() - self.coordinates.x(),
                              event.pos().y() - self.coordinates.y())
        cursor = self.mapToGlobal(event.pos())
        selected = self.page_viewer.selected_marks() + self.get_selected_rulers()
        for m in selected:
            m.move(delta)
        self.coordinates = event.pos()

    # should be here to navigate when focused
    def keyPressEvent(self, event):
        self.page_viewer.keyPressEvent(event)

    def update(self):
        super(QImageLabel, self).update()
        # synchronize paragraph_marks data
        self.page_viewer.update_paragraphs(self.paragraph_marks)

    # returns True if all marked paragraphs have both start and end marks. Useful when
    # saving result
    def verify_mark_pairs(self):
        return all(map(lambda (x, y): y is not None,
                       self.paragraph_marks.values()))

    # here data is received from bookviewer as dict { page: list of marks }
    # (useful when loading markup)
    def reload_markup(self, book_viewer_paragraphs):
        self.paragraph_marks = {}
        for pagenum, marks in book_viewer_paragraphs.items():
            for mark in marks:
                try:
                    (start, no_end) = self.paragraph_marks[mark.cas_id]
                    self.paragraph_marks[mark.cas_id] = (start, mark)
                except KeyError:
                    self.paragraph_marks[mark.cas_id] = (mark, None)
        print self.paragraph_marks

    def get_available_marks(self, cas_id):
        both = ["start", "end"]
        end_only = ["end"]
        start_only = ["start"]
        try:
            (start, end) = self.paragraph_marks[cas_id]
            if not start and not end:
                return both
            if not start:
                return start_only
            if not end:
                return end_only
            return None
        except KeyError:
            return both

    def add_ruler(self, ruler):
        self.rulers.append(ruler)

    # add mark to a correct place (start comes first, end - second)
    def add_mark(self, mark):
        toc_elem = self.get_toc_elem(mark)
        try:
            (start, end) = self.paragraph_marks[mark.cas_id]
            if start and end:
               # already have paragraph start and paragraph end
                return
            if not start and isinstance(mark, QStartParagraph):
                start = mark
            elif not end and isinstance(mark, QEndParagraph):
                end = mark
            self.paragraph_marks[mark.cas_id] = (start, end)
            # set correct states
            if not end or not start:
                toc_elem.mark_not_finished()
            else:
                toc_elem.mark_finished()
        except KeyError:
            self.paragraph_marks[mark.cas_id] = (mark, None)
            toc_elem.mark_not_finished()

    # delete mark from a tuple. if all marks have been deleted, remove that key
    # from paragraps_marks
    def delete_mark(self, mark):
        toc_elem = self.get_toc_elem(mark)
        if mark.cas_id in self.paragraph_marks.keys():
            (start, end) = self.paragraph_marks[mark.cas_id]
            if start == mark:
                self.paragraph_marks[mark.cas_id] = (None, end)
            elif end == mark:
                self.paragraph_marks[mark.cas_id] = (start, None)
            toc_elem.mark_not_finished()
        if self.paragraph_marks[mark.cas_id] == (None, None):
            del self.paragraph_marks[mark.cas_id]
            toc_elem.mark_not_started()

    def delete_ruler(self, ruler):
        self.rulers.remove(ruler)

    # here point comes in GLOBAL coordinates, among sets a list of marks to look
    # through. If no list is given, will search among marks on current page
    # (excluding rulers)
    def find_at_point(self, point, among=[]):
        def contains(mark, point):
            if mark is not None and mark.contains(point):
                print "EXACT match for %s" % mark.name
                return mark

        def intersects(mark, rect):
            if mark is not None and mark.intersects(rect):
                print "NON-EXACT match for %s" % mark.name
                return mark

        # in order to be a bit more user-friendly, first search precisely at
        # point clicked, then add some delta and search withing +-delta area
        point = self.mapFromGlobal(point)
        page_marks = self.page_viewer.get_current_page_marks() \
            if among == [] else among
        exact_match = next(
            (mark for mark in page_marks if contains(mark, point)), None)
        if exact_match:
            return exact_match
        else:
            ne_rect = QtCore.QRect(
                QtCore.QPoint(point.x() - QParagraphMark.SELECT_DELTA,
                              point.y() - QParagraphMark.SELECT_DELTA),
                QtCore.QPoint(point.x() + QParagraphMark.SELECT_DELTA,
                              point.y() + QParagraphMark.SELECT_DELTA))
            return next(
            (mark for mark in page_marks if intersects(mark, ne_rect)), None)

    # find any selected mark at point, either a paragraph mark or a ruler
    # point - in GLOBAL coordinates
    def find_any_at_point(self, point):
        selected_mark = self.find_at_point(point)
        if selected_mark:
            return selected_mark
        else:
            return self.find_at_point(point, self.get_rulers())
