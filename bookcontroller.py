#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import make_paragraph_mark, make_ruler_mark, \
    QParagraphMark, QRulerMark, QEndParagraph, QStartParagraph, QZoneMark
from tocelem import QTocElem
from markertocelem import QMarkerTocElem, QZone


# here main logic is stored. Passed to all views (BookViewerWidget,
# QImagelabel). Keeps track of paragraphs per page (parapraphs attr) and total
# paragraph marks (total marks per paragraph)
class BookController(object):
    # selection creation mode
    MODE_SECTIONS = "normal_sections"
    MODE_MARKER = "normal_marker"
    MODE_MARK = "mark"
    MODE_RULER_HOR = QRulerMark.ORIENT_HORIZONTAL
    MODE_RULER_VERT = QRulerMark.ORIENT_VERTICAL
    # zooming
    MAX_SCALE = 5
    MIN_SCALE = 1
    ZOOM_DELTA = 0.5
    # viewport delta
    VIEWPORT_DELTA = 5
    # auto

    def __init__(self, cms_course_toc, doc_processor=None):
        self.dp = doc_processor
        self.course_toc = cms_course_toc
        # marks per paragraph.
        # { paragraph_id: { marks: (start, end) }, zones: [] }
        self.paragraph_marks = {}
        # first page has number 1.
        # Paragraph per page. {pagenum : {marks: [], zones: []}
        self.paragraphs = {}
        # a list of QTocElems as they appear in listView
        self.toc_elems = []
        # a list of QMarkerTocElems (elem+objectlist) as they appear in treeView
        self.marker_toc_elems = []
        # dict of interactive objects per lesson: {paragraph_id: [objects]}
        self.objects = {}
        self.create_toc_elems()
        # a list of all rulers present
        self.rulers = []
        # zoom scale
        self.scale = 1.0
        # QTocElem currently selected
        self.current_toc_elem = None
        # adding start\end or zones
        self.operational_mode = self.MODE_SECTIONS
        # add mark mode (adding paragraph marks or rulers)
        self.mark_mode = self.MODE_MARK
        # only for start\end marks, not rulers
        self.any_unsaved_changes = False

    ### properties section
    @property
    def is_toc_selected(self):
        return self.current_toc_elem is not None

    # returns current page number + 1, as poppler ordering starts from 0, but
    # our first page has number 1
    @property
    def pagenum(self):
        if not self.dp:
            return 0
        return self.dp.curr_page_number + 1

    @property
    def selected_marks(self):
        return [m for m in self.get_current_page_marks() if m.is_selected]

    @property
    def selected_rulers(self):
        return [r for r in self.rulers if r.is_selected]

    @property
    def selected_marks_and_rulers(self):
        return self.selected_marks + self.selected_rulers

    ### setters section
    def set_horizontal_ruler_mode(self):
        self.mark_mode = self.MODE_RULER_HOR

    def set_vertical_ruler_mode(self):
        self.mark_mode = self.MODE_RULER_VERT

    def set_normal_section_mode(self):
        self.operational_mode = self.MODE_SECTIONS

    def set_normal_marker_mode(self):
        self.operational_mode = self.MODE_MARKER

    def set_current_toc_elem(self, elem):
        self.current_toc_elem = elem

    ### predicates section

    # validate that selection is in pdf's viewport
    def _is_in_pdf_bounds(self, pos):
        img = self.get_image()
        if not img:
            return
        img = img.rect()
        viewport = QtCore.QRect(img.x(),
                               img.y() + self.VIEWPORT_DELTA,
                               img.width(),
                               img.height() - self.VIEWPORT_DELTA)
        if type(pos) == QtCore.QPoint:
            return viewport.contains(pos)
        elif type(pos) == QtCore.QRect:
            return viewport.intersects(pos)
        else:
            return False

    def is_in_viewport(self, pos):
        if self.is_section_mode():
            return self._is_in_pdf_bounds(pos)
        else:
            # get mark's start\end and calculate available viewport
            if not self.current_toc_elem:
                return False
            (start, end) = \
                self.paragraph_marks[self.current_toc_elem.cas_id]["marks"]
            if start.page == end.page and end.page == self.pagenum:
                if pos.y() < start.y() or pos.y() > end.y():
                    return False
            else:
                if end.page < self.pagenum or start.page > self.pagenum:
                    print "pages"
                    return False
                current = filter(lambda m: m in [start, end],
                                 self.get_start_end_marks(self.pagenum))
                print current
                # no marks -> in between pages, True
                if len(current) == 0:
                    return True
                if current[0] == start and pos.y() < start.y():
                    print "high "
                    return False
                if current[0] == end and pos.y() > end.y():
                    print "low "
                    return False
            return True

    def is_section_mode(self):
        return self.operational_mode == self.MODE_SECTIONS

    def is_markup_mode(self):
        return self.operational_mode == self.MODE_MARKER

    def is_ruler_mode(self):
        return self.mark_mode == self.MODE_RULER_HOR or \
            self.mark_mode == self.MODE_RULER_VERT

    def is_normal_mode(self):
        return self.mark_mode == self.MODE_MARK

    def is_file_given(self):
        return self.dp is not None

    ### getters section
    def get_rulers(self):
        return self.rulers

    def get_total_pages(self):
        if self.dp:
            return self.dp.totalPages
        return 0

    def get_image(self):
        if not self.dp:
            return None
        return self.dp.curr_page(self.scale)

    def get_toc_elems(self):
        return self.toc_elems

    def get_page_marks(self, page_num):
        try:
            if self.is_section_mode():
                return self.paragraphs[page_num]["marks"]
            else:
                return self.paragraphs[page_num]["zones"]
        except KeyError:
            return []

    def get_start_end_marks(self, page_num):
        try:
            return self.paragraphs[page_num]["marks"]
        except KeyError:
            return []

    def get_current_page_marks(self):
        return self.get_page_marks(self.pagenum)

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_toc_elem(self, cas_id):
        return next((elem for (i, elem) in enumerate(self.toc_elems) \
                     if elem.cas_id == cas_id), None)

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_marker_toc_elem(self, cas_id):
        return next((elem for elem in self.marker_toc_elems \
                     if elem.cas_id == cas_id), None)

    # returns mark following given mark for toc elem with given cas-id. Used in
    # bookviewer in order to implement human-friendly navigation to start\end
    # marks when clicked on toc elem
    # no mark given means that we should take first paragraph mark found
    def get_next_paragraph_mark(self, cas_id, mark=None):
        try:
            (start, end) = self.paragraph_marks[cas_id]["marks"]
            return next(
                (m for m in [start, end] if m != mark and m is not None), mark)
        except KeyError:
            return mark

    # returns zoom's order num in list to set up in combo box
    def get_current_zoom_index(self):
        doubled_list = range(self.MIN_SCALE * 2,
                             self.MAX_SCALE * 2, int(self.ZOOM_DELTA * 2))
        try:
            return  doubled_list.index(int(self.scale * 2))
        except ValueError:
            return 0 if self.scale < self.MIN_SCALE else len(doubled_list) - 1

    # had to do this cumbersome trick as python range doesn't accept floats
    def get_all_zoom_values(self):
        return [ str(zoom * 100 / 2) + "%" for zoom in \
                range(self.MIN_SCALE * 2,
                      self.MAX_SCALE * 2,
                      int(self.ZOOM_DELTA * 2)) ]

    def get_first_error_mark(self):
        error_elem =  next((e for e in self.toc_elems if e.is_error()),
                           None)
        if not error_elem:
            return None
        return self.get_next_paragraph_mark(error_elem.cas_id)

    def get_total_error_count(self):
        return len(filter(lambda e:e.is_error(), self.toc_elems))

    def get_available_marks(self, cas_id):
        both = ["start", "end"]
        end_only = ["end"]
        start_only = ["start"]
        try:
            (start, end) = self.paragraph_marks[cas_id]["marks"]
            if not start and not end:
                return both
            if not start:
                return start_only
            if not end:
                return end_only
            return None
        except KeyError:
            return both

    ### different operations
    def open_file(self, filename):
        # TODO check that file is truly a pdf file
        self._clear_paragraph_data()
        # deselect all in toc list
        for elem in self.toc_elems:
            elem.set_not_started()
        try:
            self.dp = DocumentProcessor(filename)
            return True
        except Exception:
            # TODO eliminate catch them all
            return False

    # here marks_parent is a parent widget to set at marks' creation
    def load_markup(self, filename, marks_parent):
        self._clear_paragraph_data()
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # generate start\end marks from paragraphs' data
        for cas_id, data in paragraphs.items():
            marks = data["marks"]
            zones = data["zones"]
            for m in marks:
                page = int(m["page"])
                mark = make_paragraph_mark(parent=marks_parent,
                                           cas_id=cas_id,
                                           name=m["name"],
                                           pos=QtCore.QPoint(0, float(m["y"])),
                                           page=page,
                                           delete_func=self.delete_mark,
                                           type=m["type"])
                mark.adjust(self.scale)
                # mark loaded paragraphs gray
                # TODO think how to eliminate calling this func twice
                elem = self.get_toc_elem(cas_id)
                if elem:
                    elem.set_finished()
                if mark.page != self.pagenum:
                    mark.hide()
                try:
                    self.paragraphs[page]["marks"].append(mark)
                except KeyError:
                    self.paragraphs[page] = {"marks" : [mark],
                                             "zones": []}
            for z in zones:
                page = int(z["page"])
                zone = QZoneMark(parent=marks_parent,
                                 pos=QtCore.QPoint(0, float(z["y"])),
                                 lesson_id=cas_id,
                                 zone_id=z["zone-id"],
                                 page=page,
                                 delete_func=self.delete_zone,
                                 type=z["type"],
                                 number=z["number"],
                                 rubric=z["rubric"],
                                 objects=z["objects"])
                if page not in self.paragraphs.keys():
                    self._add_new_page(page)
                self.paragraphs[page]["zones"].append(zone)
                if zone.page != self.pagenum:
                    zone.hide()
        # fill parallel structure
        self._load_paragraph_marks()

    # returns full file name (with path) to file with markup
    def save(self, dirname):
        # normalize to get pdf-coordinates (save with scale=1.0)
        pdf_paragraphs = OrderedDict()
        # have to iterate over paragraphs (not paragraph_marks) to ensure
        # correct page order
        for pagenum in sorted(self.paragraphs.keys()):
            for m in self.paragraphs[pagenum]["marks"]:
                para_key = m.cas_id
                y = self.transform_to_pdf_coords(m.geometry()).y()
                mark = {"page" : m.page,
                        "name" : m.name,
                        "y": y}
                try:
                    pdf_paragraphs[para_key]["marks"].append(mark)
                except KeyError:
                    pdf_paragraphs[para_key] = {"marks": [mark],
                                                "zones": []}
        for cas_id in self.paragraph_marks.keys():
            for z in self.paragraph_marks[cas_id]["zones"]:
                y = self.transform_to_pdf_coords(z.geometry()).y()
                zone = {"n": z.number,
                        "type": z.type,
                        "page": z.page,
                        "y": y,
                        "rubric": z.rubric,
                        "objects": z.objects
                        }
                pdf_paragraphs[cas_id]["zones"].append(zone)
        if not self.dp:
            return
        self.any_unsaved_changes = False
        # if not all paragraphs have been marked -> add unfinished_ to filename
        finished = len(pdf_paragraphs) == len(self.toc_elems)
        return self.dp.save_all(dirname, pdf_paragraphs, finished=finished)

    # add paragraph mark to paragraph_marks (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[mark.page]["marks"]:
                self.paragraphs[mark.page]["marks"].append(mark)
        except KeyError:
            self.paragraphs[mark.page] = {"marks": [],
                                          "zones": []}
            self.paragraphs[mark.page]["marks"] = [mark]

    # if step_by_step is True then scale will be either increased or decreased
    # by 1. Otherwise - scale will be taken from delta: delta + old if delta in [MIN,
    # MAX], or not taken if out of bounds
    def zoom(self, delta, step_by_step=True):
        new_scale = old_scale = self.scale
        if step_by_step:
            if delta > 0:
                new_scale = self.scale + self.ZOOM_DELTA
            elif delta < 0:
                new_scale = self.scale - self.ZOOM_DELTA
        else: new_scale = delta + self.scale
        if new_scale >= self.MIN_SCALE and new_scale <= self.MAX_SCALE:
            self.scale = new_scale
            coeff = new_scale / old_scale
            # have to adjust ALL items including rulers
            for page_key in self.paragraphs.keys():
                markslist = self.paragraphs[page_key]["marks"] + \
                            self.paragraphs[page_key]["zones"]
                for m in markslist:
                    m.adjust(coeff)
            # now rulers
            for r in self.rulers:
                r.adjust(coeff)
        return self.scale

    def autozones(self, zone_parent):
        # auto place ALL autozones in ALL paragraphs that have start\end marks
        print "autozones clicked"
        for cas_id in self.paragraph_marks.keys():
            autozones = self._get_autoplaced_zones(cas_id)
            (start, end) = self.paragraph_marks[cas_id]["marks"]
            for az in autozones:
                # no autoplacement if zone already placed
                if self.is_zone_placed(cas_id, az["zone-id"]):
                    continue
                pos = QtCore.QPoint(0, start.y())
                if az["rel-start"]:
                    pos = QtCore.QPoint(0, az["rel-start"] * self.scale + start.y())
                elif az["rel-end"]:
                    # substract relative end from end-of-page y
                    pos = QtCore.QPoint(0, end.y() + az["rel-end"] * self.scale)
                zone = QZoneMark(pos,
                                 zone_parent,
                                 cas_id,
                                 az["zone-id"],
                                 az["page"],
                                 self.delete_zone,
                                 az["type"],
                                 az["objects"],
                                 az["number"],
                                 az["rubric"])
                self.add_zone(zone)
                if zone.page != self.pagenum:
                    zone.hide()

    # deselect all elems on page (both marks and rulers) if not in
    # keep_selections list
    def deselect_all(self, keep_selections = []):
        map(lambda x: x.set_selected(False),
            filter(lambda x: x not in keep_selections,
                   self.selected_marks_and_rulers))

    def hide_page_marks(self, pagenum):
        if pagenum in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[pagenum]["marks"] + \
                                    self.paragraphs[pagenum]["zones"])

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return QtCore.QRectF(
                      rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)

    def show_page_marks(self, pagenum):
        if pagenum in self.paragraphs.keys():
            map(lambda m: m.show(), self.paragraphs[pagenum]["marks"] + \
                                    self.paragraphs[pagenum]["zones"])

    def go_to_page(self, pagenum):
        # hide selections on this page
        self.hide_page_marks(self.pagenum)
        # show selections on page we are switching to
        self.show_page_marks(pagenum + 1)
        return self.dp.go_to_page(pagenum)

    # move all currently selected elems
    def move(self, delta, point):
        # if only one mark is selected at a time, the check whether we want to
        # bind it to a ruler
        if len(self.selected_marks) == 1:
            if not self.is_in_viewport(point):
                return
            # check if there are any rulers at point
            mark = self.selected_marks[0]
            ruler = self.find_at_point(point, self.rulers)
            self.any_unsaved_changes = True
            if ruler:
                mark.bind_to_ruler(ruler)
            else:
                # no ruler should be assigned to mark
                mark.unbind_from_ruler()
                mark.move(delta)
                # after mark is moved verify that start comes before end,
                # otherwise set error state
                other_mark = self.get_next_paragraph_mark(mark.cas_id, mark)
                if other_mark and other_mark != mark:
                    start = mark if isinstance(mark, QStartParagraph) \
                                 else other_mark
                    end = other_mark if start == mark else mark
                    toc_elem = self.get_toc_elem(mark.cas_id)
                    if self.verify_start_end(start, end):
                        toc_elem.set_finished()
                        self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(True)
                    else:
                        toc_elem.set_mixed_up_marks()
                        self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)
            return
        # else move as usual
        if all(map(lambda m: self.is_in_viewport(m.pos() + delta), \
                   self.selected_marks)):
            self.any_unsaved_changes = True
            for m in self.selected_marks:
                m.move(delta)
        # if rulers become invisible after move -> delete them
        for r in self.selected_rulers:
            r.move(delta)
            if not self.is_in_viewport(r.geometry()):
                # delete ruler
                r.delete()
                r.destroy()

    # delete currently selected marks on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def delete_marks(self):
        selected = self.selected_marks_and_rulers
        for m in selected:
            #TODO BAD, figure out how to do it better
            if self.is_section_mode() and isinstance(m, QParagraphMark):
                self.paragraphs[self.pagenum]["marks"].remove(m)
            elif self.is_markup_mode() and isinstance(m, QZoneMark):
                self.paragraphs[self.pagenum]["zones"].remove(m)
            m.delete()
            m.destroy()

    ### callbacks to be passed to Mark Widgets

    # delete mark from a tuple. if all marks have been deleted, remove that key
    # from paragraps_marks
    def delete_mark(self, mark):
        toc_elem = self.get_toc_elem(mark.cas_id)
        if mark.cas_id in self.paragraph_marks.keys():
            (start, end) = self.paragraph_marks[mark.cas_id]["marks"]
            if start == mark:
                self.paragraph_marks[mark.cas_id]["marks"] = (None, end)
            elif end == mark:
                self.paragraph_marks[mark.cas_id]["marks"] = (start, None)
            toc_elem.set_not_finished()
            self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)
        if self.paragraph_marks[mark.cas_id]["marks"] == (None, None):
            del self.paragraph_marks[mark.cas_id]
            toc_elem.set_not_started()
            self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)

    def delete_zone(self, zone):
        toc_elem = self.get_toc_elem(zone.cas_id)
        if zone.cas_id in self.paragraph_marks.keys():
            self.paragraph_marks[zone.cas_id]["zones"].remove(zone)

    def delete_ruler(self, ruler):
        self.rulers.remove(ruler)

    def _add_new_paragraph(self, cas_id):
        self.paragraph_marks[cas_id] = {"marks": None,
                                        "zones": []}
    def _add_new_page(self, pagenum):
        self.paragraphs[pagenum] = {"marks": [],
                                    "zones": []}

    # add mark to a correct place (start comes first, end - second)
    def add_mark(self, mark):
        toc_elem = self.get_toc_elem(mark.cas_id)
        try:
            (start, end) = self.paragraph_marks[mark.cas_id]["marks"]
            if start and end:
               # already have paragraph start and paragraph end
                return
            if not start and isinstance(mark, QStartParagraph):
                start = mark
            elif not end and isinstance(mark, QEndParagraph):
                end = mark
            self.paragraph_marks[mark.cas_id]["marks"] = (start, end)
            # set correct states
            if not end or not start:
                toc_elem.set_not_finished()
                self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)
            else:
                # check that end and start mark come in correct order
                if self.verify_start_end(start, end):
                    toc_elem.set_finished()
                    self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(True)
                else:
                    toc_elem.set_mixed_up_marks()
                    self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)
        except KeyError:
            self._add_new_paragraph(mark.cas_id)
            self.paragraph_marks[mark.cas_id]["marks"] = (mark, None)
            toc_elem.set_not_finished()
            self.get_marker_toc_elem(toc_elem.cas_id).set_selectable(False)

    def find_at_point(self, point, among=None):
        def contains(mark, point):
            if mark is not None and mark.contains(point):
                return mark

        def intersects(mark, rect):
            if mark is not None and mark.intersects(rect):
                return mark

        # in order to be a bit more user-friendly, first search precisely at
        # point clicked, then add some delta and search withing +-delta area
        page_marks = self.get_current_page_marks() if among is None else among
        exact_match = next(
            (mark for mark in page_marks if contains(mark, point)), None)
        if exact_match:
            return exact_match
        else:
            ne_rect = QtCore.QRect(
                QtCore.QPoint(point.x() - QParagraphMark.SELECT_DELTA,
                              point.y() - QParagraphMark.SELECT_DELTA),
                QtCore.QPoint(point.x() + QParagraphMark.SELECT_DELTA,
                              point.y() + QParagraphMark.SELECT_DELTA))
            return next(
            (mark for mark in page_marks if intersects(mark, ne_rect)), None)

    # returns a list of QTocElems (to fill a listView, for example)
    # has to return a new list all the time as items are owned by a model and
    # by calling
    def create_toc_elems(self):
        self.toc_elems = \
            [ QTocElem(elem["name"], elem["cas-id"]) \
             for elem in self.course_toc ]
        return self.toc_elems

    def create_marker_toc_elems(self):
        self.marker_toc_elems = \
            [ QMarkerTocElem(elem["name"], elem["cas-id"], elem["objects"]) \
              for elem in self.course_toc ]
        return self.marker_toc_elems

    # find any selected mark at point, either a paragraph mark or a ruler
    # point (section mode) or any zone (marker mode)
    def find_any_at_point(self, point):
        selected_mark = self.find_at_point(point)
        if selected_mark:
            return selected_mark
        else:
            return self.find_at_point(point, self.rulers)

    # returns True if all marked paragraphs have both start and end marks in
    # the correct order (start mark goes first).
    # Useful when saving result
    def verify_mark_pairs(self):
        paired = all(map(lambda (x, y): y is not None and x is not None,
                         [data["marks"] for data in self.paragraph_marks.values()]))
        if not paired:
            return False
        return all(map(lambda (x, y): self.verify_start_end(x, y),
                       [data["marks"] for data in self.paragraph_marks.values()]))

    def verify_start_end(self, start, end):
        # marks are on the same page, compare y coordinate
        if start.page == end.page and start.y() >= end.y():
            return False
        elif start.page > end.page:
            return False
        return True

    ### helper functions
    def _clear_paragraph_data(self):
        # destroy previous marks
        for page in self.paragraphs.keys():
            marks = self.paragraphs[page]["marks"]
            zones = self.paragraphs[page]["zones"]
            map(lambda m: m.destroy(), marks)
            map(lambda z: z.destroy(), zones)
        self.paragraphs = {}
        # destroy previous rulers
        for r in self.rulers:
            r.destroy()
        self.rulers = []

    # add zone to zones on page zone.page AND to paragraph's zones
    # There might be no marks on pages, so have to check on pagenum's presence
    # in self.paragraphs' keys
    def add_zone(self, zone):
        if zone.page not in self.paragraphs.keys():
            self._add_new_page(zone.page)
        self.paragraphs[zone.page]["zones"].append(zone)
        # situation with paragraph_marks is different: zones can't be placed
        # unless paragraph has start and end mark -> no check here
        self.paragraph_marks[zone.cas_id]["zones"].append(zone)

    def is_zone_placed(self, cas_id, zone_id):
        if cas_id in self.paragraph_marks.keys():
            return zone_id in \
                [z.zone_id for z in self.paragraph_marks[cas_id]["zones"]]
        return False

    def _create_mark_section_mode(self, pos, mark_parent):
        mark = None
        if self.is_normal_mode() and self.is_toc_selected:
            self.any_unsaved_changes = True
            toc_elem = self.current_toc_elem
            key = toc_elem.cas_id
            (start, end) = (None, None)
            mark_type = self.get_available_marks(key)
            if not mark_type:
                return None
            mark = make_paragraph_mark(pos,
                                       mark_parent,
                                       toc_elem.cas_id,
                                       toc_elem.name,
                                       self.pagenum,
                                       self.delete_mark,
                                       mark_type[0])
            self.add_mark(mark)
            self.add_paragraph_mark(mark)
        elif self.is_ruler_mode():
            mark = make_ruler_mark(pos,
                                   mark_parent,
                                   "",
                                   self.delete_ruler,
                                   self.mode)
            self.rulers.append(mark)
        return mark

    def _create_mark_marker_mode(self, pos, mark_parent):
        mark = None
        if self.is_normal_mode() and self.is_toc_selected:
            self.any_unsaved_changes = True
            toc_elem = self.current_toc_elem
            # TODO think of making it better
            if not isinstance(toc_elem, QZone):
                return None
            if self.is_zone_placed(toc_elem.cas_id, toc_elem.zone_id):
                return None
            zone = QZoneMark(pos,
                             mark_parent,
                             toc_elem.cas_id,
                             toc_elem.zone_id,
                             self.pagenum,
                             self.delete_zone,
                             toc_elem.type,
                             toc_elem.objects_as_dictslist(),
                             toc_elem.number,
                             toc_elem.pdf_rubric)
            self.add_zone(zone)
            print self.paragraphs
        elif self.is_ruler_mode():
            mark = make_ruler_mark(pos,
                                   mark_parent,
                                   "",
                                   self.delete_ruler,
                                   self.mode)
            self.rulers.append(mark)
        return mark

    # Callback for on click marl creation, either start\end or ruler in SECTION
    # mode or a zone in MARKUP
    def _create_mark_on_click(self, pos, mark_parent):
        # else create new one if any TOC elem selected and free space for
        # start\end mark available
        if not self.is_in_viewport(pos):
            return None
        mark = self._create_mark_section_mode(pos, mark_parent) \
                    if self.is_section_mode() \
                    else self._create_mark_marker_mode(pos, mark_parent)
        return mark

    def _get_autoplaced_zones(self, cas_id):
        # verify that everything ok with start\end
        if self.get_toc_elem(cas_id).is_finished():
            toc_elem = self.get_marker_toc_elem(cas_id)
            return toc_elem.get_autozones_as_dict()
        return []

    # here data is received from bookviewer as dict
    # { page: { marks: [], zones: [] }}
    # (useful when loading markup)
    def _load_paragraph_marks(self):
        self.paragraph_marks = {}
        for pagenum in self.paragraphs.keys():
            marks = self.paragraphs[pagenum]["marks"]
            zones = self.paragraphs[pagenum]["zones"]
            for mark in marks:
                try:
                    (start, no_end) = self.paragraph_marks[mark.cas_id]["marks"]
                    self.paragraph_marks[mark.cas_id]["marks"] = (start, mark)
                except KeyError:
                    self._add_new_paragraph(mark.cas_id)
                    self.paragraph_marks[mark.cas_id]["marks"] = (mark, None)
            # no KeyError: cas-id already added
            map(lambda z: self.paragraph_marks[mark.cas_id]["zones"].append(z),
                zones)
        print self.paragraph_marks
