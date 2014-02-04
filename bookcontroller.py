#!/usr/bin/env python
# -*- coding: utf-8 -*-
from documentprocessor import DocumentProcessor, LoaderError
from paragraphmark import make_paragraph_mark, QParagraphMark, QRulerMark
from tocelem import QTocElem


# here main logic is stored. Passed to all views (BookViewerWidget,
# QImagelabel). Keeps track of paragraphs per page (parapraphs attr) and total
# paragraph marks (total marks per paragraph)
class BookController(object):
    MODE_NORMAL = "normal"
    MODE_RULER_HOR = QRulerMark.ORIENT_HORIZONTAL
    MODE_RULER_VERT = QRulerMark.ORIENT_VERTICAL

    def __init__(self, cms_course_toc, doc_processor=None):
        # marks per paragraph. { paragraph_id: (start, end) }
        self.paragraph_marks = {}
        # first page has number 1.
        # Paragraph per page. {pagenum : [marks]}
        self.paragraphs = {}
        # a list of QTocElems as they appear in listView
        self.toc_elems = [ QTocElem(elem["name"], elem["cas-id"], i) \
                          for (i, elem) in enumerate(cms_course_toc) ]
        # a list of all rulers present
        self.rulers = []
        self.dp = doc_processor

    def set_horizontal_ruler_mode(self):
        self.mode = self.MODE_RULER_HOR

    def set_vertical_ruler_mode(self):
        self.mode = self.MODE_RULER_VERT

    def set_normal_mode(self):
        self.mode = self.MODE_NORMAL

    def get_total_pages(self):
        if self.dp:
            return self.dp.totalPages
        return 0

    # returns a list of QTocElems (to fill a listView, for example)
    def get_toc_elems(self):
        return self.toc_elems

    def get_page_marks(self, page_num):
        try:
            return self.paragraphs[str(page_num)]
        except KeyError:
            return []

    # finds toc elem ordernum by cas_id and returns corresponding QTocElem
    def get_toc_elem(self, cas_id):
        def find():
            for i, elem in enumerate(self.course_toc):
                if elem["cas-id"] == cas_id:
                    return i
            return -1
        order_num = find()
        if order_num != -1:
            return self.toc_elems[order_num]

    # returns first start\end mark for paragraph with given cas-id
    def get_first_paragraph_mark(self, cas_id):
        try:
            (start_mark, end_mark) = self.paragraph_marks[cas_id]
            return next((mark for mark in [start_mark, end_mark] if mark), None)
        except KeyError:
            return None

    def open_file(self, filename):
        self.dp = DocumentProcessor(filename)

    def load_markup(self, filename):
        # destroy previous data
        for page, marks in self.paragraphs.items():
            map(lambda m: m.destroy(), marks)
        self.paragraphs = {}
        # convert from QString
        filename = str(filename)
        paragraphs = self.dp.load_native_xml(filename)
        # clear listView and fill again with appropriate for given course-id
        # data fetched from cas
        self._fill_listview(self.course_toc)
        # generate start\end marks from paragraphs' data
        for i, (cas_id, marks) in enumerate(paragraphs.items()):
            for m in marks:
                str_page = m["page"]
                mark = make_paragraph_mark(parent=self.imageLabel,
                                           cas_id=cas_id,
                                           name=m["name"],
                                           pos=QtCore.QPoint(0, float(m["y"])),
                                           page=int(str_page),
                                           toc_num=i,
                                           type=m["type"])
                mark.adjust(self.scale)
                # mark loaded paragraphs gray
                # TODO think how to eliminate calling this func twice
                elem = self.get_toc_elem(cas_id)
                if elem:
                    elem.mark_finished()
                if mark.page != self.pageNum:
                    mark.hide()
                try:
                    self.paragraphs[str_page].append(mark)
                except KeyError:
                    self.paragraphs[str_page] = [mark]
        self.imageLabel.reload_markup(self.paragraphs)

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
        self.dp.save_all(dir_name, pdf_paragraphs)

    # returns True if all marked paragraphs have both start and end marks.
    # Useful when saving result
    def verify_mark_pairs(self):
        return all(map(lambda (x, y): y is not None,
                       self.paragraph_marks.values()))

    def get_image(self, scale):
        if not self.dp:
            return None
        return self.dp.curr_page(scale)

    def selected_marks(self):
        return [m for m in self.get_current_page_marks() if m.is_selected]

    def selected_rulers(self):
        print "selected rulers"
        res = self.imageLabel.get_selected_rulers()
        print res
        return res

    def selected_marks_and_rulers(self):
        return self.selected_marks() + self.selected_rulers()

    # add paragraph mark (without duplicates)
    def add_paragraph_mark(self, mark):
        try:
            if mark not in self.paragraphs[str(mark.page)]:
                self.paragraphs[str(mark.page)].append(mark)
        except KeyError:
            self.paragraphs[str(mark.page)] = [mark]

    def update_paragraphs(self, paragraph_marks):
        for cas_id, (start, end) in paragraph_marks.items():
            if start is not None:
                self.add_paragraph_mark(start)
                if end is not None:
                    self.add_paragraph_mark(end)

    def transform_to_pdf_coords(self, rect):
        img = self.dp.curr_page()
        if img is None:
            return QtCore.QRectF(0, 0, 0, 0)
        return QtCore.QRectF(
                      rect.x() / self.scale,
                      rect.y() / self.scale,
                      rect.width() / self.scale,
                      rect.height() / self.scale)

    def zoom(self, coeff):
        for page_key, markslist in self.paragraphs.items():
            for m in markslist:
                m.adjust(coeff)

    # deselect all elems on page (both marks and rulers) if not in
    # keep_selections list
    def deselect_all(self, keep_selections = []):
        map(lambda x: x.set_selected(False),
            filter(lambda x: x not in keep_selections,
                   self.selected_marks_and_rulers()))

    def hide_page_marks(self, pagenum):
        if str(pageNum) in self.paragraphs.keys():
            map(lambda m: m.hide(), self.paragraphs[str(pagenum)])

    def show_page_marks(self, pagenum):
        if str(pagenum) in self.paragraphs.keys():
            map(lambda m: m.show(), self.paragraphs[str(pagenum)])

    def go_to_page(self, pagenum):
        return self.dp.go_to_page(pagenum)

    # delete currently selected marks on current page. Destroy
    # widget here as well, after removing from all parallel data structures
    def delete_marks(self):
        selected = self.selected_marks_and_rulers()
        # maybe should delete things as well when right clicked on non-selected
        # area with sth present?
        #self.imageLabel.find_any_at_point(self.last_right_click)
        for m in selected:
            #TODO BAD, figure out how to do it better
            if isinstance(m, QParagraphMark):
                self.paragraphs[str(self.pageNum)].remove(m)
            m.delete()
            m.destroy()
