#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from bookcontroller import BookController
from tocelem import QTocElem
from markertocelem import QMarkerTocElem, QZone
from stylesheets import GENERAL_STYLESHEET


# this controller stores and operates with toc elems, and can match a given
# mark with a corresponding tocelem depending on operational mode
class TocController(object):
    MODE_SECTIONS = BookController.MODE_SECTIONS
    MODE_MARKUP = BookController.MODE_MARKER

    def __init__(self, course_toc):
        # store data as it comes from sectiontool -> a dict of parsed xml's
        # values
        self.course_toc = course_toc
        # course toc elems that appear in section mode (QTocElem's list)
        self.toc_elems = []
        # course toc elems that appear in markup mode (QMarkerTocElem's list)
        self.markup_toc_elems = []
        # currently selected toc_elem is stored here (regardless of mode)
        self.current_toc_elem = None
        # view for two modes
        self.sections_view = None
        self.markup_view = None

    @property
    def is_toc_selected(self):
        return self.current_toc_elem is not None

    def is_zone(self, toc_elem):
        return isinstance(toc_elem, QZone)

    def is_contents(self, toc_elem):
        return isinstance(toc_elem, QTocElem)

    def set_views(self, sections_view, markup_view):
        self.sections_view = sections_view
        self.markup_view = markup_view

    def current_toc_elems(self, mode):
        if mode == self.MODE_SECTIONS:
            return self.toc_elems
        else:
            return self.markup_toc_elems

    # ready means that this toc can be accessed by user (toc_elem with this id
    # is in FINISHED state and markup elem can be selected)
    def set_finished_state(self, value, cas_id=None):
        cas_id = self.current_toc_elem.cas_id \
            if self.current_toc_elem else cas_id
        if cas_id:
            self._get_sections_elem(cas_id).set_finished(value)
            self._get_markup_elem(cas_id).set_finished(value)

    def set_default_state(self, cas_id=None):
        cas_id = self.current_toc_elem.cas_id \
            if self.current_toc_elem else cas_id
        if cas_id:
            self._get_sections_elem(cas_id).set_not_started()
            self._get_markup_elem(cas_id).set_not_started()

    def set_default_style(self):
        for e in self.toc_elems:
            e.set_not_started()
        for e in self.markup_toc_elems:
            e.set_not_started(False)

    # returns a list of QTocElems (to fill a listView, for example)
    # has to return a new list all the time as items are owned by a model and
    # by calling
    def create_toc_elems(self, mode):
        if mode == self.MODE_SECTIONS:
            self.toc_elems = \
                [ QTocElem(elem["name"], elem["cas-id"]) \
                for elem in self.course_toc ]
            return self.toc_elems
        else:
            self.marker_toc_elems = \
                [ QMarkerTocElem(elem["name"], elem["cas-id"], elem["objects"]) \
                for elem in self.course_toc ]
            return self.marker_toc_elems

    # finds toc elem ordernum by cas_id and returns corresponding QMarkerTocElem
    def _get_sections_elem(self, cas_id):
        return next((elem for elem in self.toc_elems \
                     if elem.cas_id == cas_id), None)

    # finds toc elem ordernum by cas_id and returns corresponding QMarkerTocElem
    def _get_markup_elem(self, cas_id):
        return next((elem for elem in self.marker_toc_elems \
                     if elem.cas_id == cas_id), None)

    # finds zone in given lesson (cas_id) with given zone_id
    def get_zone_toc_elem(self, cas_id, zone_id):
        toc_elem = self.get_marker_toc_elem(cas_id)
        if toc_elem:
            return toc_elem.get_zone(zone_id)

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_elem(self, cas_id, mode):
        if mode == self.MODE_SECTIONS:
            return self._get_sections_elem(cas_id)
        else:
            return self._get_markup_elem(cas_id)

    def get_elem_for_mark(self, mark, mode):
        # if mark is a QStart\QEndParagraph mark -> return QTocElem,
        # else return QZone
        if isinstance(mark, QZone):
            return self.get_zone_toc_elem(mark.cas_id, mark.zone_id)
        else:
            return self.get_elem(mark.cas_id, mode)

    def get_total_error_count(self, mode):
        return len(filter(lambda e:e.is_error(), self.current_toc_elems(mode)))

    def get_first_error_msg(self, mode):
        error = self.get_first_error_elem(mode)
        return u"" if not error else error.get_message()

    def get_first_error_elem(self, mode):
        return next((e for e in self.current_toc_elems(mode) if e.is_error()),
                    None)

    def get_autoplaced_zones(self, cas_id):
        # verify that everything ok with start\end
        if self._get_sections_elem(cas_id).is_finished():
            return self._get_markup_elem(cas_id).get_autozones_as_dict()
        return []

    def get_view_widget(self, mode):
        if mode == self.MODE_SECTIONS:
            return self.sections_view
        return self.markup_view

    def get_selected(self, mode):
        idx = self.get_view_widget(mode).selectedIndexes()
        if len(idx) > 0:
            self.current_toc_elem = \
                self.get_view_widget(mode).model().itemFromIndex(idx[0])
            return self.current_toc_elem
        return None

    def fill_with_data(self, mode):
        view = self.get_view_widget(mode)
        model = view.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for item in self.create_toc_elems(mode):
            model.appendRow(item)
        view.setModel(model)
        self.current_toc_elem = None

    def process_selected(self, mode):
        view = self.get_view_widget(mode)
        view.setStyleSheet(GENERAL_STYLESHEET)
        current = self.get_selected(mode)
        if isinstance(current, QMarkerTocElem):
            # disable other elems and open-up toc-elem list
            view.collapseAll()
            view.expand(current.index())
        elif isinstance(current, QZone) and current.isSelectable():
            self.current_toc_elem = current

    def process_mode_switch(self, old_mode, new_mode):
        old_toc = self.get_selected(old_mode)
        new_view = self.get_view_widget(new_mode)
        self.current_toc_elem = None
        # highlight corresponding elem according to last selection in prev.tab
        if old_toc:
            toc_elem = self.get_elem(old_toc.cas_id, new_mode)
            new_view.setCurrentIndex(toc_elem.index())
            self.process_selected(new_mode)

    # now highlight first met marks' toc-elem
    # TODO NO DAMNED PARAGRAPHS HIGHLIGHTING WITHOUT THOROUGH THINKING
    # OVER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # first search among zone-marks, then among start/end
    def process_go_to_page(self, mark, mode):
        view = self.get_view_widget(mode)
        if mark:
            toc_elem = self.get_elem_for_mark(mark, mode)
            view.scrollTo(toc_elem.index())
            view.setCurrentIndex(toc_elem.index())
            self.highlight_selected_readonly(mode)
        else:
            self.dehighlight(mode)

    def process_navigate_to_error(self, error_mark, mode):
        view = self.get_view_widget(mode)
        toc_elem = self.get_elem_for_mark(error_mark, mode)
        view.scrollTo(toc_elem.index())
        view.setCurrentIndex(toc_elem.index())
        self.current_toc_elem = toc_elem

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
