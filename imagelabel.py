#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from timelogger import TimeLogger

tlogger = TimeLogger()


class QParagraphMark(QtCore.QObject):
    def __init__(self, pos, parent, toc_elem, page, type):
        super(QParagraphMark, self).__init__(parent)
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Line, parent)
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(0, pos.y()),
                                           QtCore.QSize(parent.width(),
                                                        2)))
        self.mark.show()
        self.toc_elem = toc_elem
        self.label = QtGui.QLabel(
            "%s of paragraph %s" % (type, self.toc_elem["name"]), parent)
        self.label.adjustSize()
        self.label.setGeometry(self.mark.x(),
                               self.mark.y(),
                               self.label.width(),
                               self.label.height())
        self.label.show()
        self.page = page

    def hide(self):
        self.mark.hide()
        self.label.hide()

    def show(self):
        self.mark.show()
        self.label.show()


class QStartParagraph(QParagraphMark):
    def __init__(self, pos, parent, toc_elem, page):
        super(QStartParagraph, self).__init__(pos, parent, toc_elem, page, "start")

class QEndParagraph(QParagraphMark):
    def __init__(self, pos, parent, toc_elem, page):
        super(QEndParagraph, self).__init__(pos, parent, toc_elem, page, "end")


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
        if self.page_viewer.is_toc_selected:
            toc_elem = self.page_viewer.get_selected_toc_elem()
            page = self.page_viewer.pageNum
            key = toc_elem["cas-id"]
            if key in self.paragraph_marks.keys():
                if len(self.paragraph_marks[key]) == 1:
                    self.paragraph_marks[key].append(QEndParagraph(event.pos(),
                                                                   self,
                                                                   toc_elem,
                                                                   page))
            else:
                self.paragraph_marks[key] = [QStartParagraph(event.pos(),
                                                             self,
                                                             toc_elem,
                                                             page)]
        self.update()

    def update(self):
        super(QImageLabel, self).update()
        # synchronize paragraph_marks data
        self.page_viewer.update_paragraphs(self.paragraph_marks)
