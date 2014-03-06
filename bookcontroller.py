#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import QParagraphMark, QRulerMark, QEndParagraph, \
    QStartParagraph, QZoneMark, QPassThroughZoneMark, MarkCreator
from tocelem import QTocElem, QMarkerTocElem, QZone
from zonetypes import ZONE_ICONS

# here main logic is stored. Passed to all views (BookViewerWidget,
# QImagelabel). Keeps track of paragraphs per page (parapraphs attr) and total
# marks per paragraph (paragraph_marks attr)
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

    def __init__(self, toc_controller, params, display_name, filename=None,
                 mark_creator=None):
        self.dp = DocumentProcessor(filename, display_name) \
            if filename else None
        self.toc_controller = toc_controller
        self.mc = mark_creator or MarkCreator()
        self.display_name = display_name
        # marks per paragraph.
        # { paragraph_id: { marks: (start, end) }, zones: [] }
        self.paragraph_marks = {}
        # first page has number 1.
        # Paragraph per page. {pagenum : {marks: [], zones: []}
        # IMPORTANT! Mind that this dict doesn't get updated on move()
        # operations -> need to sort elems by y() if want correct order
        self.paragraphs = OrderedDict()
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
        self.margin_width = params["margin-width"]
        self.default_zone_width = params["zone-width"]
        self.first_page = params["first-page"]
        self.pass_through_zones = params["passthrough-zones"]
        self.start_autozones = params["start-autozones"]
        self.end_autozones = params["end-autozones"]

    ### properties section
    @property
    def current_toc_elem(self):
        return self.toc_controller.active_elem

    # returns current page number + 1, as poppler ordering starts from 0, but
    # our first page has number 1
    @property
    def pagenum(self):
        if not self.dp:
            return 0
        return self.dp.curr_page_number + 1

    @property
    def markup_finished(self):
        finished = [e for e in \
                    self.toc_controller.current_toc_elems(self.MODE_MARKER)
                    if e.is_finished()]
        return len(finished) == \
            len(self.toc_controller.current_toc_elems(self.MODE_MARKER))

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
        return "r" in self.margins

    def has_left_margin(self):
        return "l" in self.margins

    def has_both_margins(self):
        return self.has_left_margin() and self.has_right_margin()

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
                return [z for z in self.paragraphs[page_num]["zones"]]
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
        self.delete_all()
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
        self.delete_all()
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # generate start\end marks from paragraphs' data
        for i, (cas_id, data) in enumerate(paragraphs.items()):
            marks = data["marks"]
            zones = data["zones"]
            for m in marks:
                page = int(m["page"])
                mark = self.mc.make_paragraph_mark(parent=marks_parent,
                                      cas_id=cas_id,
                                      name=m["name"],
                                      pos=QtCore.QPoint(0, float(m["y"])),
                                      page=page,
                                      delete_func=self.delete_mark,
                                      type=m["type"],
                                      corrections=self._get_corrections())
                mark.adjust(self.scale)
                if mark.page != self.pagenum:
                    mark.hide()
                self.add_mark(mark)
            # now generate zones
            for z in zones:
                page = int(z["page"])
                pages = {}
                for z1 in z["placements"]:
                    pages[int(z1["page"])] = float(z1["y"])
                zone = self.mc.make_zone_mark(parent=marks_parent,
                                      pos=QtCore.QPoint(0, float(z["y"])),
                                      cas_id=cas_id,
                                      zone_id=z["zone-id"],
                                      page=page,
                                      pages=pages,
                                      delete_func=self.delete_zone,
                                      number=z["number"],
                                      rubric=z["rubric"],
                                      objects=z["objects"],
                                      margin=z["at"],
                                      pass_through=z["passthrough"],
                                      corrections=self._get_corrections(
                                          z["at"], z["rubric"]))
                self.add_zone(zone)
                if self.is_markup_mode and zone.should_show(self.pagenum):
                    zone.show()
                else:
                    zone.hide()

    def _get_page_margin(self, page):
        for margin in ["l", "r"]:
            if all(map(lambda z: z.margin==margin,
                       self.paragraphs[page]["zones"])):
                return margin
        return "lr"

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
                pdf_paragraphs[cas_id]["zones"].append(z.to_dict())

        # pass first page orientation
        pdf_paragraphs["pages"] = OrderedDict()
        for page in range(1, self.dp.totalPages):
            pdf_paragraphs["pages"][page] = self._get_page_margin(page) \
                if page in self.paragraphs.keys() \
                else ["r", "l"][pagenum % 2]
        self.any_unsaved_changes = False
        # if not all paragraphs have been marked -> add unfinished_ to filename
        return self.dp.save_all(path_to_file, pdf_paragraphs)

    # add zone to zones on page zone.page AND to paragraph's zones
    # There might be no marks on pages, so have to check on pagenum's presence
    # in self.paragraphs' keys
    def add_zone(self, zone):
        def _add_to_page(pagenum):
            if pagenum not in self.paragraphs.keys():
                self._add_new_page(pagenum)
            self.paragraphs[pagenum]["zones"].append(zone)
        # if zone is a passthrough one, then add it to all it's pages
        if not zone.pass_through:
            _add_to_page(zone.page)
        else:
            map(lambda p: _add_to_page(p), zone.pages)
        # situation with paragraph_marks is different: zones can't be placed
        # unless paragraph has start and end mark -> no check here
        # TODO
        if zone.cas_id not in self.paragraph_marks:
            self._add_new_paragraph(zone.cas_id)
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
                self.any_unsaved_changes = True
                pos = QtCore.QPoint(0, start.y())
                if az["rel-start"]:
                    pos = QtCore.QPoint(0, az["rel-start"] * self.scale + start.y())
                elif az["rel-end"]:
                    # substract relative end from end-of-page y
                    pos = QtCore.QPoint(0, end.y() + az["rel-end"] * self.scale)
                margin = self._guess_margin(pos)
                # autozones are bound to START\END, not PAGE NUM in oid!
                page = start.page if az["rubric"] in self.start_autozones \
                    else end.page
                # create zone of proper type
                pass_through = az["rubric"] in self.pass_through_zones
                pages = None
                if pass_through:
                    pages = range(start.page, end.page)
                    # figure out whether should add last page
                    if end.y() > pos.y():
                        pages.append(end.page)
                    pages = dict(zip(pages, [pos.y()]*len(pages)))
                zone = self.mc.\
                    make_zone_mark(pos=pos,
                                    parent=zone_parent,
                                    cas_id=cas_id,
                                    zone_id=az["zone-id"],
                                    page=page,
                                    delete_func=self.delete_zone,
                                    objects=az["objects"],
                                    number=az["number"],
                                    rubric=az["rubric"],
                                    margin=margin,
                                    corrections=self._get_corrections(
                                        margin, az["rubric"]),
                                    auto=True,
                                    pass_through=pass_through,
                                    pages=pages)
                self.add_zone(zone)
                zone.set_page(self.pagenum)
                if zone.should_show(self.pagenum):
                    zone.show()
                else:
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
            for zone in self.paragraphs[pagenum]["zones"]:
                zone.hide()

    def hide_marks(self, pagenum):
        if pagenum in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[pagenum]["marks"])

    def show_page_marks(self, pagenum):
        show_marks = []
        if pagenum in self.paragraphs.keys():
            show_marks = self.paragraphs[pagenum]["marks"]
            if self.is_markup_mode():
                show_marks = show_marks + self.paragraphs[pagenum]["zones"]
                # for passthrough zones
                map(lambda z: z.set_page(pagenum),
                    self.paragraphs[pagenum]["zones"])
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

    def delete_all(self):
        for cas_id in self.paragraph_marks.keys():
            self.delete_marks(marks=self.paragraph_marks[cas_id]["marks"])
            self.toc_controller.set_default_state(cas_id)
        self.paragraphs = {}
        # destroy previous rulers
        for r in self.rulers:
            r.destroy()
        self.rulers = []

    # delete currently selected marks on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def delete_marks(self, forced=False, marks=None):
        marks = marks or self.selected_marks_and_rulers
        for m in marks:
            if isinstance(m, QZoneMark):
                if forced:
                    for page in m.pages:
                        self.paragraphs[page]["zones"].remove(m)
                    m.remove_pages()
                else:
                    self.paragraphs[self.pagenum]["zones"].remove(m)
                    m.remove_page(m.page)
            elif isinstance(m, QParagraphMark):
                self.paragraphs[m.page]["marks"].remove(m)
                # remove all placed zones as well if any mark removed
                for z in self.paragraph_marks[m.cas_id]["zones"]:
                    for page in z.pages:
                        self.paragraphs[page]["zones"].remove(z)
                    z.delete()
                    z.destroy()
                    self.toc_controller.process_zone_deleted(z)
                self.paragraph_marks[m.cas_id]["zones"] = []
            m.hide()
            if m.delete():
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
        return True

    # return value (True/False) means whether widget has to be physically
    # destroyed
    def delete_zone(self, zone):
        if not zone.can_be_removed():
            return False
        if zone.cas_id in self.paragraph_marks.keys():
            self.paragraph_marks[zone.cas_id]["zones"].remove(zone)
        self.toc_controller.process_zone_deleted(zone)
        return True

    def delete_ruler(self, ruler):
        self.rulers.remove(ruler)
        return True

    # add mark to a correct place (start comes first, end - second)
    def add_mark(self, mark):
        toc_elem = self.toc_controller.get_elem(mark.cas_id,
                                                self.operational_mode)
        self._add_paragraph_mark(mark)
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
            mark = self.mc.\
                make_paragraph_mark(pos, mark_parent, toc_elem.cas_id,
                                    toc_elem.name, self.pagenum,
                                    self.delete_mark, mark_type[0],
                                    corrections=self._get_corrections())
            self.add_mark(mark)
        elif self.is_ruler_mode():
            mark = self.mc.make_ruler_mark(pos, mark_parent, "",
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
                             toc_elem.objects_as_dictslist(),
                             toc_elem.number,
                             toc_elem.pdf_rubric,
                             margin=margin,
                             corrections= \
                             self._get_corrections(margin, toc_elem.pdf_rubric))
            self.add_zone(zone)
            zone.show()
        # no rulers in marker mode
        return zone

    def _guess_margin(self, pos):
        if self.has_both_margins():
            if pos.x() <= self.get_image().width() / 2:
                return "l"
            else:
                return "r"
        # else only one margin
        return self.margins[0]

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

    # get (y-coordinate, width correction) for markup mode depending on margins
    def _get_corrections(self, margin=None, rubric=None):
        width = self.default_zone_width \
            if not rubric else ZONE_ICONS[rubric].width()
        if not margin:
            if self.has_both_margins():
                return (0, 2 * self.margin_width)
            if self.has_left_margin() or self.has_right_margin():
                return (0, self.margin_width)
            return (0, 0)
        else:
            delta = (self.margin_width - width) / 2
            if margin == "r" and self.has_both_margins():
                return (self.margin_width + self.get_image().width() + delta,
                        0)
            if margin == "r":
                return (self.get_image().width() + delta, 0)
            return (delta, 0)

    # add paragraph mark to paragraph_marks (without duplicates)
    def _add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[mark.page]["marks"]:
                self.paragraphs[mark.page]["marks"].append(mark)
        except KeyError:
            self.paragraphs[mark.page] = {"marks": [mark],
                                          "zones": []}
