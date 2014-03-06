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

    def set_state(self, value, cas_id, is_ok=False, braces_err=False):
        pass

    def process_zone_added(self, zone):
        print "%s has been added" % zone.name


# an object representing mark but without all QWidget stuff
class MockMark(object):
    def __init__(self, *args, **kwargs):
        self.pos = kwargs.get("pos")
        self.corrections = kwargs.get("corrections") or (0, 0)
        self.corrected = False
        self.is_selected = False
        self.pass_through = kwargs.get("pass_through") or False
        self.auto = kwargs.get("auto") or False
        self.page = kwargs.get("page") or 0
        self.pages = kwargs.get("pages") or [self.page]
        self.cas_id = kwargs.get("cas_id")
        self.delete_func = kwargs.get("delete_func") or None
        self.type = kwargs.get("type")

    @property
    def name(self):
        return "mock object (%s): %s" % (self.type, self.cas_id)

    def y(self):
        x, y = self.pos
        return y

    def show(self):
        return "shown!"

    def hide(self):
        return "hidden!"

    def adjust(self, scale):
        return "adjusting to scale %d" % scale

    def should_show(self, page):
        return True

    def is_paragraph(self):
        return self.type != "ruler"

    def is_start(self):
        return self.type == "start"

    def is_end(self):
        return self.type == "end"

    def is_zone(self):
        return self.type == "zone"

    def is_passthrough_zone(self):
        return self.pass_through


class MockMarkCreator(object):
    def _create_mark(self, *args, **kwargs):
        return MockMark(*args, **kwargs)

    def make_paragraph_mark(self, *args, **kwargs):
        mark = self._create_mark(*args, **kwargs)
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

    def test_add_marks(self):
        # zone addition: test that proper keys appear in
        # paragraphs\parapgraph_marks and that behaviour is ok for both
        # pass_through and non-pass through zones
        # Pass through zones should appear on every paragraph page

        # mind that zone marks can't be added unless start AND end marks exist.
        # If any mark (start\end) has been deleted, then all zones are deleted
        # as well

        self.assertTrue(self.controller.paragraphs == {})
        self.assertTrue(self.controller.paragraph_marks == {})
        start_data = {"pos": (0, 10),
                      "parent": "MockParent",
                      "cas_id": "lesson:bla-bla-bla",
                      "page": 5,
                      "delete_func": lambda x: x,
                      "name": "lesson blablabla. Paragraph 2",
                      "type": "start"}
        start = self.controller.add_mark(start_data)
        self.assertTrue(start.page, 5)
        self.assertTrue(start.cas_id in self.controller.paragraph_marks)
        self.assertEqual(self.controller.paragraph_marks[start.cas_id],
                         {"marks": (start, None), "zones": []})
        # check that mark is in paragraphs
        self.assertTrue(start.page in self.controller.paragraphs)
        self.assertEquals(self.controller.paragraphs[start.page],
                          {"marks": [start], "zones": []})
        # now add end mark
        end_data = {"pos": (0, 190),
                    "parent": "MockParent",
                    "cas_id": "lesson:bla-bla-bla",
                    "page": 25,
                    "delete_func": lambda x: x,
                    "name": "lesson blablabla. Paragraph 2",
                    "type": "end"}

        end = self.controller.add_mark(end_data)
        self.assertTrue(end.page, 25)
        self.assertTrue(end.cas_id in self.controller.paragraph_marks)
        self.assertEqual(self.controller.paragraph_marks[end.cas_id],
                         {"marks": (start, end), "zones": []})
        # check that mark is in paragraphs
        self.assertTrue(end.page in self.controller.paragraphs)
        self.assertEquals(self.controller.paragraphs[end.page],
                          {"marks": [end], "zones": []})
        # try to add duplicate end mark, make sure that nothing has changed
        m = self.controller.add_mark(end_data)
        self.assertEqual(m, None)
        self.assertEqual(self.controller.paragraph_marks[end.cas_id],
                         {"marks": (start, end), "zones": []})

        # TODO continue with add zone tests
        zone_data = {"pos": (45, 20),
                     "parent": "MockParent",
                     "cas_id": "lesson:bla-bla-bla",
                     "zone_id": "01int",
                     "page": 12,
                     "delete_func": lambda x: x,
                     "objects":[ {"oid": "195-12-01-01-int",
                                  "block-id": "some block id"}],
                     "number": 1,
                     "rubric": "int",
                     "margin": "l",
                     "pass_through": False}
        zone = self.controller.add_zone(zone_data)
        self.assertTrue(zone.page in self.controller.paragraphs)
        self.assertEqual(self.controller.paragraphs[zone.page],
                         {"marks": [], "zones": [zone]})


if __name__ == '__main__':
    unittest.main()
