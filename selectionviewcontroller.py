#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from markertocelem import QZone, QMarkerTocElem
from stylesheets import GENERAL_STYLESHEET


class SelectionViewController(object):
    def __init__(self, views_dict, controller):
        self.views_dict = views_dict
        self.controller = controller
        self.mark_to_navigate = None

    def get_view_widget(self, mode):
        try:
            return self.views_dict[mode]
        except KeyError:
            return None

    def get_selected(self, mode):
        idx = self.get_view_widget(mode).selectedIndexes()
        if len(idx) > 0:
            return self.get_view_widget(mode).model().itemFromIndex(idx[0])
        return None

    # returns either QTocElem or QMarkerTocElem depend. on mode
    # FIXME no info about mode types here!
    def get_toc_elem(self, cas_id, mode):
        print mode
        if mode == "section_mode":
            return self.controller.get_toc_elem(cas_id)
        else:
            return self.controller.get_marker_toc_elem(cas_id)

    def fill_with_data(self, mode):
        view = self.get_view_widget(mode)
        model = view.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for item in self.controller.create_toc_elems(mode):
            model.appendRow(item)
        view.setModel(model)
        self.controller.set_current_toc_elem(None)

    def process_selected(self, mode):
        view = self.get_view_widget(mode)
        view.setStyleSheet(GENERAL_STYLESHEET)
        current = self.get_selected(mode)
        if current:
            self.mark_to_navigate = self.controller.\
                get_next_paragraph_mark(current, self.mark_to_navigate)
        if isinstance(current, QMarkerTocElem):
            # disable other elems and open-up toc-elem list
            view.collapseAll()
            view.expand(current.index())
        elif isinstance(current, QZone) and current.isSelectable():
            self.controller.set_current_toc_elem(current)
        else:
            # if current is None then None will be set
            self.controller.set_current_toc_elem(current)
        return self.mark_to_navigate

    def process_mode_switch(self, old_mode, new_mode):
        old_toc = self.get_selected(old_mode)
        new_view = self.get_view_widget(new_mode)
        self.controller.set_current_toc_elem(None)
        # highlight corresponding elem according to last selection in prev.tab
        if old_toc:
            toc_elem = self.get_toc_elem(old_toc.cas_id, new_mode)
            new_view.setCurrentIndex(toc_elem.index())
            self.process_selected(new_mode)

    # now highlight first met marks' toc-elem
    # TODO NO DAMNED PARAGRAPHS HIGHLIGHTING WITHOUT THOROUGH THINKING
    # OVER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # first search among zone-marks, then among start/end
    def process_go_to_page(self, pagenum, mode):
        view = self.get_view_widget(mode)
        marks = self.controller.get_page_marks(pagenum, mode)
        if marks != []:
            toc_elem = self.get_toc_elem_for_mark(marks[0])
            view.scrollTo(toc_elem.index())
            view.setCurrentIndex(toc_elem.index())
            self.highlight_selected_readonly(mode)
        else:
            self.dehighlight(mode)

    def process_navigate_to_error(self, mode):
        view = self.get_view_widget(mode)
        error = self.controller.get_first_error_mark()
        if error:
            toc_elem = self.get_toc_elem_for_mark(error)
            view.scrollTo(toc_elem.index())
            view.setCurrentIndex(toc_elem.index())
            self.controller.set_current_toc_elem(toc_elem)
        return error

    # draw nice violet selection on toc-elem with id
    # elem as current so that it can't be modified
    def highlight_selected_readonly(self, mode):
        view = self.get_view_widget(mode)
        view.setStyleSheet(
            """ QListView::item:selected{
            background-color: rgb(100, 149, 237) }
            """)

    # restore settings from general stylesheet
    def dehighlight(self, mode):
        view = self.get_view_widget(mode)
        view.setStyleSheet(GENERAL_STYLESHEET)

    def get_toc_elem_for_mark(self, mark):
        # if mark is a QStart\QEndParagraph mark -> return QTocElem,
        # else return QZone
        if isinstance(mark, QZone):
            return self.controller.get_zone_toc_elem(mark.cas_id, mark.zone_id)
        else:
            return self.controller.get_toc_elem(mark.cas_id)

    #def select(self, pagenum):
        #marks = self.controller.get_page_marks(pagenum)

    #def _select_toc_elem(self, toc_elem, mode):
        #view = self.get_view_widget(mode)
        #view.scrollTo(toc_elem.index())
        #view.setCurrentIndex(toc_elem.index())
