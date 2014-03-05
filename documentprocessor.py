# -*- coding: utf-8 -*-
import os
from popplerqt4 import Poppler
from lxml import etree
from lxml.builder import ElementMaker

XHTML_NAMESPACE = "http://internet-school.ru/abc"

E = ElementMaker(namespace=XHTML_NAMESPACE,
                 nsmap={'is' : XHTML_NAMESPACE})


class LoaderError(Exception):
    def __str__(self):
        return self.message.encode("utf-8")

class DocumentProcessor(object):
    resolution = 72.0

    def __init__(self, filename, display_name):
        self.filename = filename
        self.display_name = display_name
        self.curr_page_num = 0
        # map of maps: rendered_pages in all possible scales
        self.rendered_pages = {}
        print u"filename is %s" % filename
        # check that file exists (in case app is run from console)
        if os.path.isfile(filename):
            self.doc = Poppler.Document.load(filename)
            self.doc.setRenderHint(Poppler.Document.TextAntialiasing)
        else:
            raise LoaderError(u"No such file: %s" % filename)

    # 0 for first page
    @property
    def curr_page_number(self):
        return self.curr_page_num

    @property
    def png_prefix(self):
        return "page_"

    @property
    def totalPages(self):
        if not self.doc:
            return 0
        return self.doc.numPages()

    def width(self, scale=1):
        return self.curr_page(scale).width()

    def height(self, scale=1):
        return self.curr_page(scale).height()

    # returns a QImage
    def render_page(self, num, scale):
        page = self.doc.page(num)
        qimage = page.renderToImage(self.resolution * scale,
                                  self.resolution * scale,
                                  0,
                                  0,
                                  page.pageSize().width() * scale,
                                  page.pageSize().height() * scale,
                                  0)
        return qimage

    def next_page(self):
        self.curr_page_num = self.curr_page_num + 1 \
                             if self.curr_page_num < self.doc.numPages() - 1 \
                             else self.doc.numPages() - 1
        return self.curr_page()

    def prev_page(self):
        self.curr_page_num = self.curr_page_num - 1 if self.curr_page_num > 0 \
                                                    else 0
        return self.curr_page()

    # here 1st page is passed as page 0
    def go_to_page(self, pagenum):
        self.curr_page_num = pagenum if pagenum in range(0, self.totalPages) \
                                     else self.curr_page_num
        return self.curr_page() if self.curr_page_num == pagenum else None

    def curr_page(self, scale=1):
        # if page has already been rendered -> take from rendered dict
        if self.curr_page_num in self.rendered_pages.keys():
            # search for prerendered scale
            page_scales = self.rendered_pages[self.curr_page_num]
            if scale not in page_scales.keys():
                self.rendered_pages[self.curr_page_num][scale] = \
                    self.render_page(self.curr_page_num, scale)
        else:
            rendered = self.render_page(self.curr_page_num, scale)
            self.rendered_pages[self.curr_page_num] = { scale : rendered }
        return self.rendered_pages[self.curr_page_num][scale]

    # selection is a QRect
    def get_text(self, selection):
        if not selection:
            return ""
        return unicode(self.doc.page(self.curr_page_num).text(selection))

    # returns a dict of {cas-id : paragraph marks data} (the same used in
    # bookviewer as self.paragraphs)
    # filename = name of file with markup, NOT pdf
    def load_native_xml(self, filename):
        tree = etree.parse(filename)
        PAGES_XPATH = "/is:object/is:text/is:ebook-pages/is:ebook-page"
        PARAGRAPHS_XPATH = "/is:object/is:text/is:ebook-pages/is:ebook-para"
        paragraphs = tree.xpath(PARAGRAPHS_XPATH,
                           namespaces = { "is" : XHTML_NAMESPACE})
        out_paragraphs = {}
        for paragraph in paragraphs:
            cas_id = paragraph.get("id")
            name = paragraph.get("name")
            start_y = paragraph.get("start-y")
            start_page = paragraph.get("start-page")
            end_y = paragraph.get("end-y")
            end_page = paragraph.get("end-page")
            start = {"cas-id": cas_id,
                     "name" : name,
                     "y": start_y,
                     "page": start_page,
                     "type": "start"}
            end = {"cas-id": cas_id,
                   "name" : name,
                   "y": end_y,
                   "page": end_page,
                   "type": "end"}
            zones = []
            for zone in paragraph.xpath("is:ebook-zone",
                                        namespaces = { "is" : XHTML_NAMESPACE}):
                objects = [{"oid": o.get("oid"),
                            "block-id": o.get("block-id")}
                           for o in zone.xpath("is:ebook-object",
                                               namespaces = { "is" : XHTML_NAMESPACE})]
                placements = [{"page": pl.get("page"),
                               "y": pl.get("y")}
                              for pl in zone.xpath("is:ebook-placement",
                                                   namespaces = { "is" : XHTML_NAMESPACE})
                             ]
                page = zone.get("page") or next((z["page"] for z in placements),
                                                None)
                def _get_zone_id():
                    return zone.get("rubric") if zone.get("n") in ["00", None] \
                        else zone.get("n") + zone.get("rubric")
                new_zone = {"cas-id": cas_id,
                            "zone-id": _get_zone_id(),
                            "page": page,
                            "type": zone.get("type"),
                            "rubric": zone.get("rubric"),
                            "placements": placements,
                            "number": zone.get("n"),
                            "y": zone.get("y"),
                            "at": zone.get("at"),
                            "objects": objects,
                            "passthrough": zone.get("type") == u"repeat"}
                zones.append(new_zone)
            out_paragraphs[cas_id] = { "marks": [start, end],
                                       "zones": zones }
        return out_paragraphs

    # Paragraphs - a dict {cas-id : dict with all paragraph data}
    def gen_native_xml(self, paragraphs, progress):
        PAGES = E("ebook-pages", src=self.filename)
        ICON_SET = E("ebook-icon-set")
        PAGES.append(ICON_SET)
        # add paragraphs info
        for cas_id, data in paragraphs.items():
            # make sure that no paragraphs are saved without end mark
            marks = data.get("marks", None)
            if not marks:
                continue
            zones = data.get("zones", [])
            assert len(marks) == 2, \
                "Some paragraphs don't have end marks, can't save that way!"
            PARA = E("ebook-para", id=str(cas_id),
                     **{ "start-page": str(marks[0]["page"]),
                         "start-y": str(marks[0]["y"]),
                         "name": marks[0]["name"],
                         "end-page": str(marks[1]["page"]),
                         "end-y": str(marks[1]["y"]) })
            for zone in zones:
                # passthrough zones come first
                if zone["type"] == "repeat":
                    ZONE = E("ebook-zone", type="repeat",
                             **{"y": str(zone["y"]),
                                "rubric": zone["rubric"],
                                "at": zone["at"]})
                    for pl in zone["placements"]:
                        ZONE.append(E("ebook-placement",
                                    **{"page": str(pl["page"]),
                                       "y": str(pl["y"])}))
                else:
                    ZONE = E("ebook-zone", type=zone["type"],
                            **{ "n": str(zone["n"]),
                                "page": str(zone["page"]),
                                "y": str(zone["y"]),
                                "rubric": zone["rubric"],
                                "at": zone["at"]})
                for obj in zone["objects"]:
                    ZONE.append(E("ebook-object",
                                  **{ "oid": obj["oid"],
                                     "block-id": obj["block-id"] }))
                PARA.append(ZONE)
            PAGES.append(PARA)

        # TODO can take a lot of time (esp. when rendering differently sized
        # pages), show progress here
        if progress:
            progress.setRange(1, self.totalPages)
        for page in range(1, self.totalPages):
            margin = paragraphs["pages"][page]
            def _get_page_preview_str(page):
                return "page-" + "0"*(3-len(str(page))) + str(page) + ".png"

            PAGE = E("ebook-page",
                     **{ "preview": _get_page_preview_str(page),
                         "n": str(page),
                         "width": str(self.width()),
                         "height": str(self.height()),
                         "hide": "false",
                         "zone-margins": margin,
                         "fold": margin })
            PAGES.append(PAGE)
            if progress:
                progress.setValue(page)
        root = E.object(E.text(PAGES), **{"display-name": self.display_name})
        result = etree.tostring(root, pretty_print=True, encoding="utf-8")
        return result

    def gen_toc_xml(self):
        # returns last page processed
        def _process_child(fc, prefix="", prev_page=1):
            i = 1
            previous_page = prev_page
            while not fc.isNull():
                elem = fc.toElement()
                # tex-like section-ref
                destination = elem.attribute("DestinationName")
                pagenum = self.doc.linkDestination(destination).pageNumber()
                previous_page = pagenum
                if fc.hasChildNodes():
                    previous_page = _process_child(fc.firstChild(),
                                                   prefix=prefix+"%d." % i,
                                                   prev_page=previous_page)
                fc = fc.nextSibling()
                i = i + 1
            return previous_page


        toc = self.doc.toc()
        if not toc:
            return
        _process_child(toc.firstChild())

    # generates and saves previes, returns a list of generated filenames
    def gen_previews(self, path):
        filenames = []
        save_path = path[:-1] if path[-1]=='/' else path
        for i, png in enumerate(self._render_all_to_png(), start=1):
            name = os.path.join(save_path, self.png_prefix + str(i))
            filenames.append(name)
            png.save(name, "png")
        return filenames

    def save_all(self, path_to_file, paragraphs, progress=None):
        with open(path_to_file, 'w') as fname:
            fname.write(self.gen_native_xml(paragraphs, progress))
        return path_to_file

    def _processTextBlocks(self):
        result = dict()
        for i in range(0, self.doc.numPages()):
            result[i] = [ ( ( t.boundingBox().left(),
                              t.boundingBox().top(),
                              t.boundingBox().width(),
                              t.boundingBox().height() ),
                             unicode(t.text()) )
                          for t in self.doc.page(i).textList()]
        return result

    def _render_one_to_png(self, num):
        return self.doc.page(num).renderToImage()

    def _render_all_to_png(self):
        return [self._render_one_to_png(i)
                for i in range(0, self.doc.numPages())]
