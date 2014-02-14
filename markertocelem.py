#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class QObjectElem(QtGui.QStandardItem):
    def __init__(self, oid, type):
        super(QObjectElem, self).__init__()
        self.type = type
        self.oid = oid
        self.setText(oid)
        self.setEditable(False)


class QMarkerTocElem(QtGui.QStandardItem):
    def __init__(self, name, lesson_id, objects):
        super(QMarkerTocElem, self).__init__()
        self.name = name
        self.lesson_id = lesson_id
        self.objects = objects
        self.setText(name)
        self.setEditable(False)
        for obj in self.objects:
            child = QObjectElem(obj["oid"], obj["type"])
            self.appendRow(child)
