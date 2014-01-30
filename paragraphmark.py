#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore

class QParagraphMark(QtGui.QWidget):
    WIDTH = 5
    SELECT_DELTA = 12

    def __init__(self, pos, parent, cas_id, name, toc_num, page, type):
        super(QParagraphMark, self).__init__(parent)
        self.mark = QtGui.QRubberBand(QtGui.QRubberBand.Line, parent)
        self.mark.setGeometry(QtCore.QRect(QtCore.QPoint(0, pos.y()),
                                           QtCore.QSize(parent.width(),
                                                        QParagraphMark.WIDTH)))
        self.mark.show()
        self.name = name
        self.cas_id = cas_id
        self.label = QtGui.QLabel(
            "%s of paragraph %s" % (type, self.name), parent)
        self._adjust_to_mark()
        self.label.show()
        self.page = page
        self.toc_num = toc_num
        self.type = type
        self.is_selected = False

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

    def paint_me(self, painter):
        if self.is_selected:
            painter.fillRect(self.geometry(), QtGui.QColor(0, 0, 0, 32))
            self.brush = QtGui.QBrush(QtCore.Qt.red)
            pal = QtGui.QPalette()
            pal.setBrush(QtGui.QPalette.Base, self.brush);
            self.mark.setPalette(pal);
        else:
            painter.fillRect(self.geometry(), QtGui.QColor(180, 180, 180, 32))
        self.update()

    def update(self):
        self.mark.update()
        self.label.update()

    def contains(self, cursor):
        return self.geometry().contains(cursor)

    def intersects(self, rect):
        return self.geometry().intersects(rect)

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


