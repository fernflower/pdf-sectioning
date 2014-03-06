# -*- coding: utf-8 -*-
import unittest
import sys
from documentprocessor import DocumentProcessor
from bookcontroller import BookController
from bookviewerwidget import BookViewerWidget
from sectiontool import SectionTool


class MocTocController(object):
    def get_elem(self, cas_id, mode):
        return None

    def set_state(self, value, cas_id):
        pass

    def process_zone_added(self, zone):
        print "%s has been added" % zone.name


# an object representing mark but without all QWidget stuff
class MockMark(object):
    def __init__(self, *args, **kwargs):
        self.corrections = kwargs.get("corrections") or (0, 0)
        self.corrected = False
        self.is_selected = False
        self.pass_through = kwargs.get("pass_through") or False
        self.auto = kwargs.get("auto") or False
        self.page = kwargs.get("page") or 0
        self.pages = kwargs.get("pages") or [self.page]
        self.cas_id = kwargs.get("cas_id")
        self.delete_func = kwargs.get("delete_func") or None
        self.type = ""

    @property
    def name(self):
        return "mock object (%s): %s" % (self.type, self.cas_id)

    def show(self):
        return "shown!"

    def hide(self):
        return "hidden!"

    def adjust(self, scale):
        return "adjusting to scale %d" % scale

    def should_show(self, page):
        return True


class MockMarkCreator(object):
    def _create_mark(self, *args, **kwargs):
        return MockMark(*args, **kwargs)

    def make_paragraph_mark(self, *args, **kwargs):
        mark = self._create_mark(*args, **kwargs)
        mark.type = "paragraph"
        return mark

    def make_ruler_mark(self, *args, **kwargs):
        mark = self._create_mark(*args, **kwargs)
        mark.type = "ruler"
        return mark

    def make_zone_mark(self, *args, **kwargs):
        mark = self._create_mark(*args, **kwargs)
        mark.type = "zone"
        return mark


# figure out that cas-xml is loaded and parsed properly
class DocLoaderTest(unittest.TestCase):

    def setUp(self):
        super(DocLoaderTest, self).setUp()
        self.markup_file = "tests/native-test.xml"
        self.display_name = "Chemistry-8 course"
        self.pdf_file = "tests/chemistry8.pdf"
        self.st = SectionTool(u"tests/config-test")
        self.mc = MockMarkCreator()
        self.toc_controller = MocTocController()
        self.controller = BookController(toc_controller=self.toc_controller,
                                         params=self.st._defaults,
                                         display_name=self.display_name,
                                         filename=self.pdf_file,
                                         mark_creator=self.mc)

    def test_load_markup(self):
        self.controller.load_markup(self.markup_file, "MockParent")
        # 16 paragraphs with data and 2 dataless ones in the beginning
        self.assertEqual(len(self.controller.paragraph_marks.keys()), 18)


if __name__ == '__main__':
    unittest.main()
