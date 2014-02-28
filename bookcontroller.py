#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import make_paragraph_mark, make_ruler_mark, \
    QParagraphMark, QRulerMark, QEndParagraph, QStartParagraph, QZoneMark
from tocelem import QTocElem, QMarkerTocElem, QZone
from zonetypes import ZONE_ICONS


# here main logic is stored. Passed to all views (BookViewerWidget,
# QImagelabel). Keeps track of paragraphs per page (parapraphs attr) and total
# paragraph marks (total marks per paragraph)
class BookController(object):
    # selection creation mode
    MODE_SECTIONS = "section_mode"
    MODE_MARKER = "markup_mode"
    MODE_MARK = "mark"
    MODE_RULER_HOR = QRulerMark.ORIENT_HORIZONTAL
    MODE_RULER_VERT = QRulerMark.ORIENT_VERTICAL
    # zooming
    MAX_SCALE = 5
    MIN_SCALE = 1
    ZOOM_DELTA = 0.5
    # viewport delta
    VIEWPORT_DELTA = 5
    # margins
    LEFT = "l"
    RIGHT = "r"
    LEFT_RIGHT = "lr"
    FIRST_PAGE = LEFT
    MARGIN_WIDTH = 50
    # if no image found -> default
    ZONE_WIDTH = 20


    def __init__(self, toc_controller, params, doc_processor, display_name):
        self.dp = doc_processor
        self.toc_controller = toc_controller
        self.display_name = display_name
        # marks per paragraph.
        # { paragraph_id: { marks: (start, end) }, zones: [] }
        self.paragraph_marks = {}
        # first page has number 1.
        # Paragraph per page. {pagenum : {marks: [], zones: []}
        # IMPORTANT! Mind that this dict doesn't get updated on move()
        # operations -> need to sort elems by y() if want correct order
        self.paragraphs = OrderedDict()
        # dict of interactive objects per lesson: {paragraph_id: [objects]}
        self.objects = {}
        # a list of all rulers present
        self.rulers = []
        # zoom scale
        self.scale = 1.0
        # adding start\end or zones
        self.operational_mode = self.MODE_SECTIONS
        # add mark mode (adding paragraph marks or rulers)
        self.mark_mode = self.MODE_MARK
        # only for start\end marks, not rulers
        self.any_unsaved_changes = False
        # margins and first marked page orientation stuff
        self.margins = params["margins"]
        self.first_page = params["first-page"]

    # get (y-coordinate, width correction) for markup mode depending on margins
    def _get_corrections(self, margin=None, rubric=None):
        width = self.ZONE_WIDTH if not rubric else ZONE_ICONS[rubric].width()
        if not margin:
            if self.has_both_margins():
                return (0, 2 * self.MARGIN_WIDTH)
            if self.has_left_margin() or self.has_right_margin():
                return (0, self.MARGIN_WIDTH)
            return (0, 0)
        else:
            delta = (self.MARGIN_WIDTH - width) / 2
            if margin == self.RIGHT and self.has_both_margins():
                return (self.MARGIN_WIDTH + self.get_image().width() + delta,
                        0)
            if margin == self.RIGHT:
                return (self.get_image().width() + delta, 0)
            return (delta, 0)

    ### properties section
    @property
    def current_toc_elem(self):
        return self.toc_controller.current_toc_elem

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
        return [r for r in self.get_rulers() if r.is_selected]

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
        self.mark_mode = self.MODE_MARK
        for r in self.rulers:
            r.show()
        # no zones here
        self.hide_zones(self.pagenum)

    def set_normal_marker_mode(self):
        self.operational_mode = self.MODE_MARKER
        self.mark_mode = self.MODE_MARK
        # no rulers here
        for r in self.rulers:
            r.hide()
        # show hidden zones
        self.show_page_marks(self.pagenum)

    ### predicates section

    # validate that selection is in pdf's viewport
    def is_zone_placed(self, cas_id, zone_id):
        if cas_id in self.paragraph_marks.keys():
            return zone_id in \
                [z.zone_id for z in self.paragraph_marks[cas_id]["zones"]]
        return False

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
                    return False
                current = filter(lambda m: m in [start, end],
                                 self.get_start_end_marks(self.pagenum))
                # no marks -> in between pages, True
                if len(current) == 0:
                    return True
                if current[0] == start and pos.y() < start.y():
                    return False
                if current[0] == end and pos.y() > end.y():
                    return False
            return True

    def has_right_margin(self):
        return self.margins == self.RIGHT or self.has_both_margins()

    def has_left_margin(self):
        return self.margins == self.LEFT or self.has_both_margins()

    def has_both_margins(self):
        return self.margins == self.LEFT_RIGHT

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
        return self.rulers if self.is_section_mode() else []

    def get_total_pages(self):
        if self.dp:
            return self.dp.totalPages
        return 0

    def get_image(self):
        if not self.dp:
            return None
        return self.dp.curr_page(self.scale)

    def get_page_marks(self, page_num, mode):
        try:
            if mode == self.MODE_SECTIONS:
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
        return self.get_page_marks(self.pagenum, self.operational_mode)

    # returns mark following given mark for toc elem with given cas-id. Used in
    # bookviewer in order to implement human-friendly navigation to start\end
    # marks when clicked on toc elem
    # no mark given means that we should take first paragraph mark found
    def _get_next_start_end(self, cas_id, mark):
        try:
            (start, end) = self.paragraph_marks[cas_id]["marks"]
            return next(
                (m for m in [start, end] if m != mark and m is not None),
                mark)
        except KeyError:
            return mark

    def _get_zone(self, cas_id, zone_id):
        try:
            return next(
                 (z for z in self.paragraph_marks[cas_id]["zones"] \
                  if z.zone_id == zone_id),
                 None)
        except KeyError:
            return None

    # return first mark corr. to selected toc not equal to mark
    def get_next_paragraph_mark(self, mode, mark=None):
        toc_elem = self.toc_controller.active_elem
        if not toc_elem:
            return None
        return self.get_mark_for_toc_elem(mode, toc_elem, mark)

    # A vital method for toc -> mark retrieval
    def get_mark_for_toc_elem(self, mode, toc_elem, not_this_one=None):
        if mode == self.MODE_SECTIONS:
            return self._get_next_start_end(toc_elem.cas_id, not_this_one)
        else:
            if self.toc_controller.is_contents(toc_elem):
                return self._get_next_start_end(toc_elem.cas_id, not_this_one)
            elif self.toc_controller.is_zone(toc_elem):
                return self._get_zone(toc_elem.cas_id, toc_elem.zone_id)

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

    def get_first_error_mark(self, mode):
        error_toc = self.toc_controller.get_first_error_elem(mode)
        return self.get_mark_for_toc_elem(mode, error_toc)

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
    def open_file(self, filename, progress=None):
        # TODO check that file is truly a pdf file
        self._clear_paragraph_data()
        # deselect all in toc list
        self.toc_controller.set_default_style()
        try:
            self.dp = DocumentProcessor(filename, self.display_name)
            return True
        except Exception as e:
            print e.message
            # TODO eliminate catch them all
            return False

    # here marks_parent is a parent widget to set at marks' creation
    def load_markup(self, filename, marks_parent, progress=None):
        self._clear_paragraph_data()
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # generate start\end marks from paragraphs' data
        for i, (cas_id, data) in enumerate(paragraphs.items()):
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
                                           type=m["type"],
                                           corrections=self._get_corrections())
                mark.adjust(self.scale)
                # mark loaded paragraphs gray
                # TODO think how to eliminate calling this func twice
                self.toc_controller.set_state(True, cas_id)
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
                                 objects=z["objects"],
                                 margin=z["at"],
                                 corrections=self._get_corrections(z["at"],
                                                                   z["rubric"]))
                if page not in self.paragraphs.keys():
                    self._add_new_page(page)
                self.paragraphs[page]["zones"].append(zone)
                if zone.page != self.pagenum:
                    zone.hide()
                self.toc_controller.process_zone_added(zone)
        # fill parallel structure
        self._load_paragraph_marks()

    def _get_page_margin(self, page):
        for margin in [self.LEFT, self.RIGHT]:
            if all(map(lambda z: z.margin==margin,
                       self.paragraphs[page]["zones"])):
                return margin
        return self.LEFT_RIGHT

    # returns full file name (with path) to file with markup
    def save(self, path_to_file, progress=None):
        if not self.dp:
            return
        # normalize to get pdf-coordinates (save with scale=1.0)
        pdf_paragraphs = OrderedDict()
        # have to iterate over paragraphs (not paragraph_marks) to ensure
        # correct page order
        for pagenum in sorted(self.paragraphs.keys()):
            for m in sorted(self.paragraphs[pagenum]["marks"],
                            key=lambda m:m.y()):
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
                        "objects": z.objects,
                        "at": z.margin }
                pdf_paragraphs[cas_id]["zones"].append(zone)

        # pass first page orientation
        pdf_paragraphs["pages"] = OrderedDict()
        for page in range(1, self.dp.totalPages):
            pdf_paragraphs["pages"][page] = self._get_page_margin(page) \
                if page in self.paragraphs.keys() \
                else [self.RIGHT, self.LEFT][pagenum % 2]
        self.any_unsaved_changes = False
        # if not all paragraphs have been marked -> add unfinished_ to filename
        finished = len(pdf_paragraphs) == \
            len(self.toc_controller.current_toc_elems(self.operational_mode))
        return self.dp.save_all(path_to_file, pdf_paragraphs,
                                finished=finished)

    # add paragraph mark to paragraph_marks (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[mark.page]["marks"]:
                self.paragraphs[mark.page]["marks"].append(mark)
        except KeyError:
            self.paragraphs[mark.page] = {"marks": [],
                                          "zones": []}
            self.paragraphs[mark.page]["marks"] = [mark]

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
        # mark corr. elem as placed
        self.toc_controller.process_zone_added(zone)

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
            for r in self.get_rulers():
                r.adjust(coeff)
        return self.scale

    def autozones(self, zone_parent, progress=None):
        # auto place ALL autozones in ALL paragraphs that have start\end marks
        for i, cas_id in enumerate(self.paragraph_marks.keys()):
            autozones = self.toc_controller.get_autoplaced_zones(cas_id)
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
                margin = self._guess_margin(pos)
                zone = QZoneMark(pos,
                                 zone_parent,
                                 cas_id,
                                 az["zone-id"],
                                 az["page"],
                                 self.delete_zone,
                                 az["type"],
                                 az["objects"],
                                 az["number"],
                                 az["rubric"],
                                 margin=margin,
                                 auto=True,
                                 corrections=self._get_corrections(margin,
                                                                   az["rubric"]))
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
        self.hide_zones(pagenum)
        self.hide_marks(pagenum)

    def hide_zones(self, pagenum):
        if pagenum in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[pagenum]["zones"])

    def hide_marks(self, pagenum):
        if pagenum in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[pagenum]["marks"])

    def show_page_marks(self, pagenum):
        if pagenum in self.paragraphs.keys():
            show_marks = self.paragraphs[pagenum]["marks"]
            if self.is_markup_mode():
                show_marks = show_marks + self.paragraphs[pagenum]["zones"]
            map(lambda m: m.show(), show_marks)

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return QtCore.QRectF(
                      rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)

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
            ruler = self.find_at_point(point, self.get_rulers())
            self.any_unsaved_changes = True
            if ruler:
                mark.bind_to_ruler(ruler)
            else:
                # no ruler should be assigned to mark
                mark.unbind_from_ruler()
                mark.move(delta)
                # after mark is moved verify that start comes before end,
                # otherwise set error state
                other_mark = self.get_next_paragraph_mark(self.operational_mode,
                                                          mark)
                if other_mark and other_mark != mark:
                    start = mark if isinstance(mark, QStartParagraph) \
                                 else other_mark
                    end = other_mark if start == mark else mark
                    toc_elem = self.toc_controller.get_elem(mark.cas_id,
                                                            self.operational_mode)
                    is_ok = self.verify_start_end(start, end)
                    (ok_braces, error) = self.verify_brackets()
                    self.toc_controller.set_state(True, mark.cas_id,
                                                  not is_ok,
                                                  not ok_braces)
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
        toc_elem = self.toc_controller.get_elem(mark.cas_id,
                                                self.operational_mode)
        if mark.cas_id in self.paragraph_marks.keys():
            (start, end) = self.paragraph_marks[mark.cas_id]["marks"]
            if start == mark:
                self.paragraph_marks[mark.cas_id]["marks"] = (None, end)
            elif end == mark:
                self.paragraph_marks[mark.cas_id]["marks"] = (start, None)
            self.toc_controller.set_state(False, mark.cas_id)
        if self.paragraph_marks[mark.cas_id]["marks"] == (None, None):
            del self.paragraph_marks[mark.cas_id]
            self.toc_controller.set_default_state()

    def delete_zone(self, zone):
        if zone.cas_id in self.paragraph_marks.keys():
            self.paragraph_marks[zone.cas_id]["zones"].remove(zone)
            self.toc_controller.process_zone_deleted(zone)

    def delete_ruler(self, ruler):
        self.rulers.remove(ruler)

    # add mark to a correct place (start comes first, end - second)
    def add_mark(self, mark):
        toc_elem = self.toc_controller.get_elem(mark.cas_id,
                                                self.operational_mode)
        self.add_paragraph_mark(mark)
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
                self.toc_controller.set_state(False, mark.cas_id)
            else:
                # check that end and start mark come in correct order
                is_ok = self.verify_start_end(start, end)
                (ok_braces, error) = self.verify_brackets()
                self.toc_controller.set_state(True, mark.cas_id,
                                              not is_ok,
                                              not ok_braces)
        except KeyError:
            self._add_new_paragraph(mark.cas_id)
            self.paragraph_marks[mark.cas_id]["marks"] = (mark, None)
            self.toc_controller.set_state(False, mark.cas_id)

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


    # find any selected mark at point, either a paragraph mark or a ruler
    # point (section mode) or any zone (marker mode)
    def find_any_at_point(self, point):
        selected_mark = self.find_at_point(point)
        if selected_mark:
            return selected_mark
        else:
            return self.find_at_point(point, self.get_rulers())

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

    # check that no paragraph begins in between other paragraph's start and end
    # the solution is similar to (({}()))()) brackets validation problem so
    # called the same
    # returns (True, None) and (False, error_mark)
    def verify_brackets(self):
        stack = []
        for pagenum in sorted(self.paragraphs.keys()):
            for m in sorted(self.paragraphs[pagenum]["marks"],
                            key=lambda m:m.y()):
                if isinstance(m, QStartParagraph):
                    stack.append(m.cas_id)
                    continue
                elif isinstance(m, QEndParagraph):
                    try:
                        if stack[-1] != m.cas_id:
                            return (False, m)
                        else:
                            stack.pop()
                    except IndexError:
                        return (False, m)
        # as braces check can be done when all paragraphs have both marks,
        # count will be always = 0
        return (True, None)

    ### helper functions
    def _add_new_paragraph(self, cas_id):
        self.paragraph_marks[cas_id] = {"marks": None,
                                        "zones": []}
    def _add_new_page(self, pagenum):
        self.paragraphs[pagenum] = {"marks": [],
                                    "zones": []}

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

    def _create_mark_section_mode(self, pos, mark_parent):
        mark = None
        if self.is_normal_mode() and self.toc_controller.is_anything_selected:
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
                                       mark_type[0],
                                       corrections=self._get_corrections())
            self.add_mark(mark)
        elif self.is_ruler_mode():
            mark = make_ruler_mark(pos,
                                   mark_parent,
                                   "",
                                   self.delete_ruler,
                                   self.mark_mode,
                                   corrections=self._get_corrections())
            self.rulers.append(mark)
        return mark

    def _create_mark_marker_mode(self, pos, mark_parent):
        mark = None
        if self.is_normal_mode() and self.toc_controller.is_anything_selected:
            self.any_unsaved_changes = True
            toc_elem = self.current_toc_elem
            # TODO think of making it better
            if not isinstance(toc_elem, QZone):
                return None
            if self.is_zone_placed(toc_elem.cas_id, toc_elem.zone_id):
                return None
            margin = self._guess_margin(pos)
            zone = QZoneMark(pos,
                             mark_parent,
                             toc_elem.cas_id,
                             toc_elem.zone_id,
                             self.pagenum,
                             self.delete_zone,
                             toc_elem.type,
                             toc_elem.objects_as_dictslist(),
                             toc_elem.number,
                             toc_elem.pdf_rubric,
                             margin=margin,
                             corrections=self._get_corrections(margin,
                                                               toc_elem.pdf_rubric))
            self.add_zone(zone)
        # no rulers in marker mode
        return zone

    def _guess_margin(self, pos):
        if self.has_both_margins():
            if pos.x() <= self.get_image().width() / 2:
                return self.LEFT
            else:
                return self.RIGHT
        return self.margins

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
            for z in zones:
                map(lambda z:
                    self.paragraph_marks[z.cas_id]["zones"].append(z), zones)
