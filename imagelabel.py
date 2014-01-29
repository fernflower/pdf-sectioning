#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from timelogger import TimeLogger

tlogger = TimeLogger()


class QParagraphMark(QtCore.QObject):
    def __init__(self, pos, parent, cas_id, name, toc_num, page, type):
        super(QParagraphMark, self).__init__(parent)
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Line, parent)
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(0, pos.y()),
                                           QtCore.QSize(parent.width(), 5)))
        self.mark.show()
        self.name = name
        self.cas_id = cas_id
        self.label = QtGui.QLabel(
            "%s of paragraph %s" % (type, self.name), parent)
        self._adjust_to_mark()
        self.label.show()
        self.page = page
        self.toc_num = toc_num

    def hide(self):
        self.mark.hide()
        self.label.hide()

    def show(self):
        self.mark.show()
        self.label.show()

    def geometry(self):
        return self.mark.geometry()

    #TODO find out how to destroy widgets
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

    # get start-y coordinate
    def y(self):
        return self.mark.pos().y()


class QStartParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, toc_num, page):
        super(QStartParagraph, self).__init__(pos,
                                              parent,
                                              cas_id,
                                              name,
                                              toc_num,
                                              page,
                                              "start")

class QEndParagraph(QParagraphMark):
    def __init__(self, pos, parent, cas_id, name, toc_num, page):
        super(QEndParagraph, self).__init__(pos,
                                            parent,
                                            cas_id,
                                            name,
                                            toc_num,
                                            page,
                                            "end")

MARKS_DICT = {"start": QStartParagraph,
              "end": QEndParagraph}

def make_paragraph_mark(pos, parent, cas_id, name, toc_num, page, type):
    return MARKS_DICT[type](pos, parent, cas_id, name, toc_num, page)


# this class manages all keys/mouse clicks and calls actions from page_viewer
# class. It keeps track of all paragraph marks with coordinates in dict, key is
# cas-id
class QImageLabel(QtGui.QLabel):
    def __init__(self, parent, page_viewer):
        self.page_viewer = page_viewer
        self.paragraph_marks = {}
        self.coordinates = None
        self.resize = False
        super(QImageLabel, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    @property
    def cursor_pos(self):
        return self.mapFromGlobal(QtGui.QCursor.pos())

    def wheelEvent(self, event):
        self.page_viewer.zoom(event.delta())
        self.update()

    # override paint event
    def paintEvent(self, event):
        super(QImageLabel, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        img = self.page_viewer.get_image()
        pixmap = QtGui.QPixmap.fromImage(img)
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())

    def mousePressEvent(self, event):
        # disable right mouse click as it shows context menu
        if event.buttons() == QtCore.Qt.RightButton:
            return super(QImageLabel, self).mousePressEvent(event)
        if self.page_viewer.is_toc_selected:
            toc_elem = self.page_viewer.get_selected_toc_elem()
            page = self.page_viewer.pageNum
            key = toc_elem.cas_id
            (start, end) = (None, None)
            if key in self.paragraph_marks.keys():
                (start, end) = self.paragraph_marks[key]
                if end is None:
                    end = QEndParagraph(event.pos(),
                                        self,
                                        toc_elem.cas_id,
                                        toc_elem.name,
                                        toc_elem.order_num,
                                        page)
                    toc_elem.mark_finished()
            else:
                start = QStartParagraph(event.pos(),
                                        self,
                                        toc_elem.cas_id,
                                        toc_elem.name,
                                        toc_elem.order_num,
                                        page)
                toc_elem.mark_not_finished()
            # add to paragraph_marks at last
            self.paragraph_marks[key] = (start, end)
        self.update()

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
