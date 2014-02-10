#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import make_paragraph_mark, make_ruler_mark, \
    QParagraphMark, QRulerMark, QEndParagraph, QStartParagraph
from tocelem import QTocElem


# here main logic is stored. Passed to all views (BookViewerWidget,
# QImagelabel). Keeps track of paragraphs per page (parapraphs attr) and total
# paragraph marks (total marks per paragraph)
class BookController(object):
    # selection creation mode
    MODE_NORMAL = "normal"
    MODE_RULER_HOR = QRulerMark.ORIENT_HORIZONTAL
    MODE_RULER_VERT = QRulerMark.ORIENT_VERTICAL
    # zooming
    MAX_SCALE = 5
    MIN_SCALE = 1
    # viewport delta
    VIEWPORT_DELTA = 5

    def __init__(self, cms_course_toc, doc_processor=None):
        self.dp = doc_processor
        self.course_toc = cms_course_toc
        # marks per paragraph. { paragraph_id: (start, end) }
        self.paragraph_marks = {}
        # first page has number 1.
        # Paragraph per page. {pagenum : [marks]}
        self.paragraphs = {}
        # a list of QTocElems as they appear in listView
        self.toc_elems = []
        self.create_toc_elems()
        # a list of all rulers present
        self.rulers = []
        # zoom scale
        self.scale = 1.0
        # QTocElem currently selected
        self.current_toc_elem = None
        # add mark mode (adding paragraph marks or rulers)
        self.mode = self.MODE_NORMAL
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

    ### setters section
    def set_horizontal_ruler_mode(self):
        self.mode = self.MODE_RULER_HOR

    def set_vertical_ruler_mode(self):
        self.mode = self.MODE_RULER_VERT

    def set_normal_mode(self):
        self.mode = self.MODE_NORMAL

    def set_current_toc_elem(self, elem):
        self.current_toc_elem = elem

    ### predicates section
    def is_ruler_mode(self):
        return self.mode == self.MODE_RULER_HOR or \
            self.mode == self.MODE_RULER_VERT

    def is_normal_mode(self):
        return self.mode == self.MODE_NORMAL

    ### getters section
    def get_selected_rulers(self):
        return [r for r in self.rulers if r.is_selected]

    def get_rulers(self):
        return self.rulers

    def get_total_pages(self):
        if self.dp:
            return self.dp.totalPages
        return 0

    def get_toc_elems(self):
        return self.toc_elems

    def get_page_marks(self, page_num):
        try:
            return self.paragraphs[str(page_num)]
        except KeyError:
            return []

    def get_current_page_marks(self):
        return self.get_page_marks(self.pagenum)

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_toc_elem(self, cas_id):
        return next((elem for (i, elem) in enumerate(self.toc_elems) \
                     if elem.cas_id == cas_id), None)

    # returns mark following given mark for toc elem with given cas-id. Used in
    # bookviewer in order to implement human-friendly navigation to start\end
    # marks when clicked on toc elem
    # no mark given means that we should take first paragraph mark found
    def get_next_paragraph_mark(self, cas_id, mark=None):
        try:
            (start, end) = self.paragraph_marks[cas_id]
            return next(
                (m for m in [start, end] if m != mark and m is not None), mark)
        except KeyError:
            return mark

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
            (start, end) = self.paragraph_marks[cas_id]
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
        self.dp = DocumentProcessor(filename)

    # here marks_parent is a parent widget to set at marks' creation
    def load_markup(self, filename, marks_parent):
        # destroy previous marks
        for page, marks in self.paragraphs.items():
            map(lambda m: m.destroy(), marks)
        self.paragraphs = {}
        # destroy previous rulers
        for r in self.rulers:
            r.destroy()
        self.rulers = []
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # generate start\end marks from paragraphs' data
        for i, (cas_id, marks) in enumerate(paragraphs.items()):
            for m in marks:
                str_page = m["page"]
                mark = make_paragraph_mark(parent=marks_parent,
                                           cas_id=cas_id,
                                           name=m["name"],
                                           pos=QtCore.QPoint(0, float(m["y"])),
                                           page=int(str_page),
                                           toc_num=i,
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
                    self.paragraphs[str_page].append(mark)
                except KeyError:
                    self.paragraphs[str_page] = [mark]
        self._load_paragraph_marks(self.paragraphs)

    # here data is received from bookviewer as dict { page: list of marks }
    # (useful when loading markup)
    def _load_paragraph_marks(self, book_viewer_paragraphs):
        self.paragraph_marks = {}
        for pagenum, marks in book_viewer_paragraphs.items():
            for mark in marks:
                try:
                    (start, no_end) = self.paragraph_marks[mark.cas_id]
                    self.paragraph_marks[mark.cas_id] = (start, mark)
                except KeyError:
                    self.paragraph_marks[mark.cas_id] = (mark, None)

    def save(self, dirname):
        # normalize to get pdf-coordinates (save with scale=1.0)
        pdf_paragraphs = {}
        for key, markslist in self.paragraphs.items():
            for m in markslist:
                para_key = m.cas_id
                mark = {"page" : m.page,
                        "name" : m.name,
                        "y": self.transform_to_pdf_coords(m.geometry()).y()}
                try:
                    pdf_paragraphs[para_key].append(mark)
                except KeyError:
                    pdf_paragraphs[para_key] = [mark]
        if not self.dp:
            return
        self.dp.save_all(dirname, pdf_paragraphs)
        self.any_unsaved_changes = False

    # returns True if all marked paragraphs have both start and end marks in
    # the correct order (start mark goes first).
    # Useful when saving result
    def verify_mark_pairs(self):
        paired = all(map(lambda (x, y): y is not None and x is not None,
                         self.paragraph_marks.values()))
        if not paired:
            return False
        return all(map(lambda (x, y): self.verify_start_end(x, y),
                       self.paragraph_marks.values()))

    def verify_start_end(self, start, end):
        # marks are on the same page, compare y coordinate
        if start.page == end.page and start.y() >= end.y():
            return False
        elif start.page > end.page:
            return False
        return True

    def get_image(self):
        if not self.dp:
            return None
        return self.dp.curr_page(self.scale)

    def selected_marks(self):
        return [m for m in self.get_current_page_marks() if m.is_selected]

    def selected_rulers(self):
        return [r for r in self.rulers if r.is_selected]

    def selected_marks_and_rulers(self):
        return self.selected_marks() + self.selected_rulers()

    # validate that selection is in pdf's viewport
    def is_in_viewport(self, pos):
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
            print "Damn it"
            return False

    # add paragraph mark to paragraph_marks (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[str(mark.page)]:
                self.paragraphs[str(mark.page)].append(mark)
        except KeyError:
            self.paragraphs[str(mark.page)] = [mark]

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return QtCore.QRectF(
                      rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)

    def zoom(self, delta):
        new_scale = old_scale = self.scale
        if delta > 0:
            new_scale = self.scale + 0.5
        elif delta < 0:
            new_scale = self.scale - 0.5
        if new_scale >= self.MIN_SCALE and new_scale <= self.MAX_SCALE:
            self.scale = new_scale
            coeff = new_scale / old_scale
            # have to adjust ALL items including rulers
            for page_key, markslist in self.paragraphs.items():
                for m in markslist:
                    m.adjust(coeff)
            # now rulers
            for r in self.rulers:
                r.adjust(coeff)

    # deselect all elems on page (both marks and rulers) if not in
    # keep_selections list
    def deselect_all(self, keep_selections = []):
        map(lambda x: x.set_selected(False),
            filter(lambda x: x not in keep_selections,
                   self.selected_marks_and_rulers()))

    def hide_page_marks(self, pagenum):
        if str(pagenum) in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[str(pagenum)])

    def show_page_marks(self, pagenum):
        if str(pagenum) in self.paragraphs.keys():
            map(lambda m: m.show(), self.paragraphs[str(pagenum)])

    def go_to_page(self, pagenum):
        return self.dp.go_to_page(pagenum)

    # move all currently selected elems
    def move(self, delta, point):
        # if only one mark is selected at a time, the check whether we want to
        # bind it to a ruler
        if len(self.selected_marks()) == 1:
            if not self.is_in_viewport(point):
                return
            # check if there are any rulers at point
            mark = self.selected_marks()[0]
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
                    else:
                        toc_elem.set_mixed_up_marks()
            return
        # else move as usual
        if all(map(lambda m: self.is_in_viewport(m.pos() + delta), \
                   self.selected_marks())):
            self.any_unsaved_changes = True
            for m in self.selected_marks():
                m.move(delta)
        # if rulers become invisible after move -> delete them
        for r in self.selected_rulers():
            r.move(delta)
            if not self.is_in_viewport(r.geometry()):
                # delete ruler
                r.delete()
                r.destroy()
                print self.rulers

    # delete currently selected marks on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def delete_marks(self):
        selected = self.selected_marks_and_rulers()
        # maybe should delete things as well when right clicked on non-selected
        # area with sth present? Sth like the following:
        #self.imageLabel.find_any_at_point(self.last_right_click)
        for m in selected:
            #TODO BAD, figure out how to do it better
            if isinstance(m, QParagraphMark):
                self.paragraphs[str(self.pagenum)].remove(m)
            m.delete()
            m.destroy()

    ### callbacks to be passed to Mark Widgets

    # delete mark from a tuple. if all marks have been deleted, remove that key
    # from paragraps_marks
    def delete_mark(self, mark):
        toc_elem = self.get_toc_elem(mark.cas_id)
        if mark.cas_id in self.paragraph_marks.keys():
            (start, end) = self.paragraph_marks[mark.cas_id]
            if start == mark:
                self.paragraph_marks[mark.cas_id] = (None, end)
            elif end == mark:
                self.paragraph_marks[mark.cas_id] = (start, None)
            toc_elem.set_not_finished()
        if self.paragraph_marks[mark.cas_id] == (None, None):
            del self.paragraph_marks[mark.cas_id]
            toc_elem.set_not_started()

    def delete_ruler(self, ruler):
        self.rulers.remove(ruler)

    # Callback for on clock marl creation, either start\end or ruler
    def _create_mark_on_click(self, pos, mark_parent):
        # else create new one if any TOC elem selected and free space for
        # start\end mark available
        if not self.is_in_viewport(pos):
            return
        if self.is_normal_mode() and self.is_toc_selected:
            self.any_unsaved_changes = True
            toc_elem = self.current_toc_elem
            key = toc_elem.cas_id
            (start, end) = (None, None)
            mark_type = self.get_available_marks(key)
            if not mark_type:
                return
            mark = make_paragraph_mark(pos,
                                       mark_parent,
                                       toc_elem.cas_id,
                                       toc_elem.name,
                                       toc_elem.order_num,
                                       self.pagenum,
                                       self.delete_mark,
                                       mark_type[0])
            self.add_mark(mark)
            self.add_paragraph_mark(mark)
        elif self.is_ruler_mode():
            mark = make_ruler_mark(pos,
                                   mark_parent,
                                   "i am a ruler",
                                   self.delete_ruler,
                                   self.mode)
            self.rulers.append(mark)

    # add mark to a correct place (start comes first, end - second)
    def add_mark(self, mark):
        toc_elem = self.get_toc_elem(mark.cas_id)
        try:
            (start, end) = self.paragraph_marks[mark.cas_id]
            if start and end:
               # already have paragraph start and paragraph end
                return
            if not start and isinstance(mark, QStartParagraph):
                start = mark
            elif not end and isinstance(mark, QEndParagraph):
                end = mark
            self.paragraph_marks[mark.cas_id] = (start, end)
            # set correct states
            if not end or not start:
                toc_elem.set_not_finished()
            else:
                # check that end and start mark come in correct order
                if self.verify_start_end(start, end):
                    toc_elem.set_finished()
                else:
                    toc_elem.set_mixed_up_marks()
        except KeyError:
            self.paragraph_marks[mark.cas_id] = (mark, None)
            toc_elem.set_not_finished()

    def find_at_point(self, point, among=None):
        def contains(mark, point):
            if mark is not None and mark.contains(point):
                print "EXACT match for %s" % mark.name
                return mark

        def intersects(mark, rect):
            if mark is not None and mark.intersects(rect):
                print "NON-EXACT match for %s" % mark.name
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
            [ QTocElem(elem["name"], elem["cas-id"], i) \
             for (i, elem) in enumerate(self.course_toc) ]
        return self.toc_elems

    # find any selected mark at point, either a paragraph mark or a ruler
    # point - in GLOBAL coordinates
    def find_any_at_point(self, point):
        selected_mark = self.find_at_point(point)
        if selected_mark:
            return selected_mark
        else:
            return self.find_at_point(point, self.rulers)
