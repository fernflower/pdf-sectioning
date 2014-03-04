#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from bookcontroller import BookController
from tocelem import QTocElem, QMarkerTocElem, QZone, QAutoZoneContainer
from paragraphmark import QParagraphMark, QZoneMark
from stylesheets import GENERAL_STYLESHEET


class DisabledZoneDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, toc_controller):
        super(DisabledZoneDelegate, self).__init__()
        self.toc_controller = toc_controller
        self.normal_brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        self.normal_pen = QtGui.QPen(QtCore.Qt.NoPen)
        self.selected_brush = QtGui.QBrush(QtGui.QColor(171, 205, 239))

    def paint(self, painter, option, index):
        parent_num = index.parent().row()
        if parent_num != -1:
            parent = index.model().itemFromIndex(index.parent())
            if isinstance(parent, QMarkerTocElem) or \
                    isinstance(parent, QAutoZoneContainer):
                zone = index.model().itemFromIndex(index)
                if not isinstance(zone, QZone):
                    super(DisabledZoneDelegate, self).paint(painter,
                                                            option, index)
                    return
                painter.save()
                painter.setPen(self.normal_pen)
                if not zone.is_on_page(self.toc_controller.pagenum_func()):
                    painter.setBrush(self.normal_brush)
                else:
                    painter.setBrush(self.selected_brush)
                zone.emitDataChanged()
                painter.drawRect(option.rect)
                painter.restore()
        super(DisabledZoneDelegate, self).paint(painter, option, index)

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
        # currently selected element (QTocElem or QZone) is stored here
        self.current_toc_elem = None
        self.pagenum_func = None
        # view for two modes
        self.sections_view = None
        self.markup_view = None

    @property
    def is_anything_selected(self):
        return self.current_toc_elem is not None

    def is_zone(self, toc_elem):
        return isinstance(toc_elem, QZone)

    def is_contents(self, toc_elem):
        return isinstance(toc_elem, QTocElem)

    @property
    def toc_elem(self):
        if self.is_toc_selected:
            return self.current_toc_elem
        else:
            return self._get_markup_elem(self.current_toc_elem.cas_id)

    @property
    def current_page(self):
        if not self.pagenum_func:
            return 0
        return self.pagenum_func()

    def set_views(self, sections_view, markup_view):
        self.sections_view = sections_view
        self.markup_view = markup_view

    # FIXME dammit, try to avoid this. Have to pass current page somehow
    # synchronized with BookViewer, could not think of a better way
    def set_pagenum_func(self, func):
        self.pagenum_func = func

    def current_toc_elems(self, mode):
        if mode == self.MODE_SECTIONS:
            return self.toc_elems
        else:
            return self.markup_toc_elems

    # return either TocElem or Zone; if clicked on a container like AutoZone,
    # then return TocElem as well. In order to get element to operate with from
    # TocController this property should be used
    @property
    def active_elem(self):
        if isinstance(self.current_toc_elem, QAutoZoneContainer):
            return self._get_markup_elem(self.current_toc_elem.cas_id)
        return self.current_toc_elem

    # ready means that this toc can be accessed by user (toc_elem with this id
    # is in FINISHED state and markup elem can be selected)
    def set_state(self, both_ends, cas_id=None, mixed_up=False,
                           brackets_err=False):
        cas_id = cas_id if cas_id else self.current_toc_elem
        if cas_id:
            value = not mixed_up and not brackets_err and both_ends
            if mixed_up:
                self._get_sections_elem(cas_id).set_mixed_up_marks()
            elif brackets_err:
                self._get_sections_elem(cas_id).set_brackets_error()
            else:
                self._get_sections_elem(cas_id).set_finished(value)
            # markup elems can be selected ONLY if appropriate start\end
            # have been set
            mtoc = self._get_markup_elem(cas_id)
            if value:
                mtoc._set_selectable(True)
            self.markup_view.setRowHidden(mtoc.index().row(),
                                          mtoc.index().parent(), not value)

    def set_default_state(self, cas_id=None):
        cas_id = self.current_toc_elem.cas_id \
            if self.current_toc_elem else cas_id
        if cas_id:
            self._get_sections_elem(cas_id).set_not_started()
            self._get_markup_elem(cas_id).set_not_started()
        self.current_toc_elem = None

    def set_default_style(self):
        for e in self.toc_elems:
            e.set_not_started()
        for e in self.markup_toc_elems:
            e.set_not_started()

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
            self.markup_toc_elems = \
                [ QMarkerTocElem(elem["name"], elem["cas-id"],
                                 elem["objects"])
                for elem in self.course_toc ]
            return self.markup_toc_elems

    # finds zone in given lesson (cas_id) with given zone_id
    def get_zone_toc_elem(self, cas_id, zone_id):
        toc_elem = self._get_markup_elem(cas_id)
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
        if isinstance(mark, QZoneMark):
            return self.get_zone_toc_elem(mark.cas_id, mark.zone_id)
        elif isinstance(mark, QParagraphMark):
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

    def fill_with_data(self, mode):
        view = self.get_view_widget(mode)
        view.reset()
        model = view.model()
        if model:
            model.clear()
        else:
            model = QtGui.QStandardItemModel()
        for item in self.create_toc_elems(mode):
            model.appendRow(item)
        view.setModel(model)
        if mode == self.MODE_MARKUP:
            dz = DisabledZoneDelegate(self)
            self.markup_view.setItemDelegate(dz)
        self.current_toc_elem = None
        # hide unfinished items
        for mtoc in self.markup_toc_elems:
            self.markup_view.setRowHidden(mtoc.index().row(),
                                          mtoc.index().parent(), True)

    def process_selected(self, mode):
        view = self.get_view_widget(mode)
        view.setStyleSheet(GENERAL_STYLESHEET)
        current = self._get_selected(mode)
        if isinstance(current, QMarkerTocElem):
            # disable other elems and open-up toc-elem list
            view.collapseAll()
            view.expand(current.index())
        elif isinstance(current, QAutoZoneContainer):
            view.expand(current.index())
            self.current_toc_elem = self._get_markup_elem(current.cas_id)
        elif isinstance(current, QZone) and current.isSelectable() or \
            isinstance(current, QTocElem):
            self.current_toc_elem = current

    def process_zone_added(self, zone):
        print "za"
        zone_elem = self.get_zone_toc_elem(zone.cas_id, zone.zone_id)
        if zone_elem:
            zone_elem.set_finished(True)
        # if all zones have been added, mark TocElem as finished as well
        self.current_toc_elem = self._get_markup_elem(zone.cas_id)
        self.current_toc_elem.set_finished(
            self.current_toc_elem.all_zones_placed)

    def process_zone_deleted(self, zone):
        zone_elem = self.get_zone_toc_elem(zone.cas_id, zone.zone_id)
        zone_elem.set_finished(False)
        # mark toc_elem as unfinished or not started
        toc_elem = self._get_markup_elem(zone.cas_id)
        toc_elem.set_finished(False)

    def process_mode_switch(self, old_mode, new_mode):
        old_toc = self._get_selected(old_mode)
        new_view = self.get_view_widget(new_mode)
        # highlight corresponding elem according to last selection in prev.tab
        if old_toc:
            toc_elem = self.get_elem(old_toc.cas_id, new_mode)
            new_view.setCurrentIndex(toc_elem.index())
            self.process_selected(new_mode)
        self.current_toc_elem = None

    # now highlight first met marks' toc-elem
    # TODO NO DAMNED PARAGRAPHS HIGHLIGHTING WITHOUT THOROUGH THINKING
    # OVER!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # first search among zone-marks, then among start/end
    def process_go_to_page(self, mark, mode):
        view = self.get_view_widget(mode)
        # make only objects on this page selectable for markup
        #if mark:
            #toc_elem = self.get_elem_for_mark(mark, mode)
            #view.scrollTo(toc_elem.index())
            #view.setCurrentIndex(toc_elem.index())
            #self.highlight_selected_readonly(mode)
        #else:
            #self.dehighlight(mode)

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

    def select_toc_for_mark(self, mark, mode):
        # rulers can't be mapped to toc-elems
        if isinstance(mark, QParagraphMark):
            view = self.get_view_widget(mode)
            toc = self.get_elem_for_mark(mark, mode)
            view.setCurrentIndex(toc.index())
            self.current_toc_elem = toc

    def _get_selected(self, mode):
        idx = self.get_view_widget(mode).selectedIndexes()
        if len(idx) > 0:
            self.current_toc_elem = \
                self.get_view_widget(mode).model().itemFromIndex(idx[0])
        else:
            self.current_toc_elem = None
        return self.current_toc_elem

    # finds toc elem ordernum by cas_id and returns corresponding QMarkerTocElem
    def _get_sections_elem(self, cas_id):
        return next((elem for elem in self.toc_elems \
                     if elem.cas_id == cas_id), None)

    # finds toc elem ordernum by cas_id and returns corresponding QMarkerTocElem
    def _get_markup_elem(self, cas_id):
        return next((elem for elem in self.markup_toc_elems \
                     if elem.cas_id == cas_id), None)
