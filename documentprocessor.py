# -*- coding: utf-8 -*-
from popplerqt4 import Poppler
from PyQt4 import QtCore
from lxml import etree
from lxml.builder import ElementMaker
from timelogger import TimeLogger

XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
E = ElementMaker(namespace=XHTML_NAMESPACE,
                 nsmap={'is' : XHTML_NAMESPACE})

tlogger = TimeLogger()

class LoaderError(Exception):
    pass

class DocumentProcessor(object):
    resolution = 72.0
    result_file_name = 'native.xml'
    toc_file_name = 'toc.xml'

    def __init__(self, filename):
        self.tlogger = TimeLogger()
        self.filename = filename
        print "filename is %s" % filename
        try:
            self.tlogger.start("load page")
            self.doc = Poppler.Document.load(filename)
            self.gen_toc_xml()
            self.tlogger.end()
        except:
            # TODO AWFUL exception handling!!!!
            raise LoaderError(u'Файла %s не существует' % filename)
        self.doc.setRenderHint(Poppler.Document.TextAntialiasing)
        self.textBlocksPerPage = self._processTextBlocks()
        self.selectionsPerPage = {}
        self.curr_page_num = 0
        # map of maps: rendered_pages in all possible scales
        self.rendered_pages = {}

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

    # returns a QImage
    def render_page(self, num, scale):
        page = self.doc.page(num)
        #tlogger.start("get QImage")
        qimage = page.renderToImage(self.resolution * scale,
                                  self.resolution * scale,
                                  0,
                                  0,
                                  page.pageSize().width() * scale,
                                  page.pageSize().height() * scale,
                                  0)
        #tlogger.end()
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

    def load_native_xml(self, filename):
        tree = etree.parse(filename)
        PAGES_XPATH = "/is:object/is:text/is:ebook-pages/is:ebook-page"
        RECTS_XPATH = "is:ebook-zones/is:ebook-zone"
        BLOCKS_XPATH = "is:ebook-rect"
        pages = tree.xpath(PAGES_XPATH, namespaces = { "is" : XHTML_NAMESPACE})
        selections = {}
        for i, page in enumerate(pages):
            selections[i] = []
            zones = page.xpath(RECTS_XPATH, namespaces = { "is" : XHTML_NAMESPACE})
            for zone in zones:
                rects = []
                link = str(zone.get("link"))
                for block in zone.xpath(BLOCKS_XPATH, namespaces = { "is" : XHTML_NAMESPACE}):
                    coord_str = str(block.get("r"))
                    coords = map(lambda x: float(x.strip()), coord_str.split(","))
                    if len(coords) != 4:
                        raise LoaderError(u"Invalid coordinates: %s" % coord_str)
                    rect = QtCore.QRect(coords[0], coords[1], coords[2], coords[3])
                    rects.append(rect)
                selections[i].append(dict(rects=rects, link=link))
        return selections

    def gen_native_xml(self, selections, pngs):
        # have to figure out how to set up PyQt4 in venv first
        # keys are page nums
        #TODO should use normal xml-processor (like one in frogstar but with lxml)
        PAGES = E("ebook-pages", src=self.filename)
        root = E.object(E.text(PAGES), display_name=self.filename)
        for i, key in enumerate(selections.keys(), start=0):
            PAGE = E("ebook-page", n=str(key), preview=pngs[i])
            TEXTBOXES = E("ebook-text-boxes")
            ZONES = E("ebook-zones")
            PAGE.append(TEXTBOXES)
            PAGE.append(ZONES)
            PAGES.append(PAGE)
            for (coords, text) in self.textBlocksPerPage[i]:
                EBOOKTEXT = E("ebook-text", r="%s, %s, %s, %s" % coords)
                EBOOKTEXT.text = text
                TEXTBOXES.append(EBOOKTEXT)
            for (link, rects) in selections[key]:
                ZONE = E("ebook-zone", link=link)
                ZONES.append(ZONE)
                for rect in rects:
                    coords_str = "%f, %f, %f, %f" % \
                            (rect.x(), rect.y(), rect.width(), rect.height())
                    ZONE.append(E("ebook-rect", r=coords_str))
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
                print "%s%d. %s || %d-%d\n" % (prefix, i, elem.tagName(),
                                             previous_page, pagenum)
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
            name = save_path + '/' + self.png_prefix + str(i)
            filenames.append(name)
            png.save(name, "png")
        return filenames

    def save_all(self, path_to_dir, selections):
        # gen previews
        pngs = self.gen_previews(path_to_dir)
        # save native xml
        filename = path_to_dir + "/" + self.result_file_name
        fname = open(filename, 'w')
        fname.write(self.gen_native_xml(selections, pngs))
        fname.close()

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
