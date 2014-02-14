#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class QTocElem(QtGui.QStandardItem):
    STATE_NOT_STARTED = "not_started"
    STATE_WRONG_START_END = "wrong_start_end"
    STATE_NOT_FINISHED = "not_finished"
    STATE_FINISHED = "finished"

    # unfortunately could not find a way of setting this up from stylesheet
    ICONS = {STATE_NOT_STARTED: "buttons/Not_done.png",
             STATE_NOT_FINISHED: "buttons/Half_done.png",
             STATE_WRONG_START_END: "buttons/Half_done.png",
             STATE_FINISHED: "buttons/All_done.png"}

    # here come error messages
    ERROR_MESSAGES = \
        { STATE_NOT_FINISHED: u"Ошибка в разметке: Не хватает одной из меток",
          STATE_WRONG_START_END: \
             u"Ошибка в разметке: конец параграфа стоит выше начала" }

    def __init__(self, name, cas_id):
        super(QTocElem, self).__init__(name)
        self.name = name
        self.cas_id = cas_id
        self.state = QTocElem.STATE_NOT_STARTED
        self.setEditable(False)
        self.update()

    def update(self):
        # set widget design according to it's state
        self.setIcon(QtGui.QIcon(self.ICONS[self.state]))

    def set_finished(self):
        self.state = QTocElem.STATE_FINISHED
        self.update()

    def set_not_finished(self):
        self.state = QTocElem.STATE_NOT_FINISHED
        self.update()

    def set_not_started(self):
        self.state = QTocElem.STATE_NOT_STARTED
        self.update()

    def set_mixed_up_marks(self):
        self.state = self.STATE_WRONG_START_END
        self.update()

    def get_message(self):
        return self.ERROR_MESSAGES[self.state]

    def is_finished(self):
        return self.state == QTocElem.STATE_FINISHED

    def is_error(self):
        return self.state == QTocElem.STATE_NOT_FINISHED or \
            self.state == QTocElem.STATE_WRONG_START_END

    def is_not_started(self):
        return self.state == QTocElem.STATE_NOT_STARTED
