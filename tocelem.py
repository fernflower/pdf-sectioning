#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class QTocElem(QtGui.QStandardItem):
    STATE_NOT_STARTED = "not_started"
    STATE_NOT_FINISHED = "not_finished"
    STATE_FINISHED = "finished"

    # unfortunately could not find a way of setting this up from stylesheet
    ICONS = {STATE_NOT_STARTED: "buttons/Not_done.png",
             STATE_NOT_FINISHED: "buttons/Half_done.png",
             STATE_FINISHED: "buttons/All_done.png"}

    def __init__(self, name, cas_id, order_num):
        super(QTocElem, self).__init__(name)
        self.name = name
        self.cas_id = cas_id
        self.order_num = order_num
        self.state = QTocElem.STATE_NOT_STARTED
        self.update()

    def update(self):
        # set widget design according to it's state
        if self.state == QTocElem.STATE_FINISHED:
            self.setSelectable(False)
        elif self.state == QTocElem.STATE_NOT_STARTED:
            self.setSelectable(True)
        # set correct state icon
        self.setIcon(QtGui.QIcon(self.ICONS[self.state]))

    def mark_finished(self):
        self.state = QTocElem.STATE_FINISHED
        self.update()

    def mark_not_finished(self):
        self.state = QTocElem.STATE_NOT_FINISHED
        self.update()

    def mark_not_started(self):
        self.state = QTocElem.STATE_NOT_STARTED
        self.update()

    def is_finished(self):
        return self.state == QTocElem.STATE_FINISHED

    def is_not_finished(self):
        return self.state == QTocElem.STATE_NOT_FINISHED

    def is_not_started(self):
        return self.state == QTocElem.STATE_NOT_STARTED
