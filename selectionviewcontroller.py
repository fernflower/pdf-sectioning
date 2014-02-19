#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


# this controller deals with proper selection handling (highlight, list\tree
# view navigation) depending on state
class SelectionViewController(object):
    def __init__(self, views_dict, controller, toc_controller):
        self.views_dict = views_dict
        self.controller = controller
        self.toc_controller = toc_controller
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

    def get_toc_elem(self, cas_id, mode):
        return self.toc_controller.get_elem(cas_id, mode)

    def fill_with_data(self, mode):
        view = self.get_view_widget(mode)
        model = view.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for item in self.toc_controller.create_toc_elems(mode):
            model.appendRow(item)
        view.setModel(model)
        self.toc_controller.set_current_toc_elem(None)

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
            self.toc_controller.set_current_toc_elem(current)
        else:
            # if current is None then None will be set
            self.toc_controller.set_current_toc_elem(current)
        return self.mark_to_navigate

    def process_mode_switch(self, old_mode, new_mode):
        old_toc = self.get_selected(old_mode)
        new_view = self.get_view_widget(new_mode)
        self.toc_controller.set_current_toc_elem(None)
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
            toc_elem = self.toc_controller.get_elem_for_mark(marks[0], mode)
            view.scrollTo(toc_elem.index())
            view.setCurrentIndex(toc_elem.index())
            self.highlight_selected_readonly(mode)
        else:
            self.dehighlight(mode)

    def process_navigate_to_error(self, mode):
        view = self.get_view_widget(mode)
        error = self.controller.get_first_error_mark(mode)
        if error:
            toc_elem = self.toc_controller.get_elem_for_mark(error, mode)
            view.scrollTo(toc_elem.index())
            view.setCurrentIndex(toc_elem.index())
            self.toc_controller.set_current_toc_elem(toc_elem)
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
