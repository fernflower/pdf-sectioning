# -*- coding: utf-8 -*-
import unittest
from documentprocessor import DocumentProcessor
from bookcontroller import BookController
from bookviewerwidget import BookViewerWidget
from sectiontool import CmsQueryModule
from toccontrollertest import MockTocController


# an object representing mark but without all QWidget stuff
class MockMark(object):
    WIDTH = 20
    HEIGHT = 2

    def __init__(self, *args, **kwargs):
        self.pos = kwargs.get("pos")
        self.corrections = kwargs.get("corrections") or (0, 0)
        self.corrected = False
        self.is_selected = False
        self.pass_through = kwargs.get("pass_through") or False
        self.auto = kwargs.get("auto") or self.pass_through
        self.inner = kwargs.get("inner") or False
        self.page = kwargs.get("page") or 0
        self.pages = kwargs.get("pages") or {self.page: self.y()}
        self.cas_id = kwargs.get("cas_id")
        self.delete_func = kwargs.get("delete_func") or None
        self.zone_id = kwargs.get("zone_id") or None
        self.type = kwargs.get("type") or None
        # no such attribute in real Mark Class, useful when testing hide\show
        # functions
        self.is_shown = True

    @property
    def name(self):
        return "mock object (%s): %s" % (self.type, self.cas_id)

    def y(self):
        x, y = self.pos
        return y

    def set_page(self, page):
        self.page = page

    def show(self):
        self.is_shown = True
        return "shown!"

    def hide(self):
        self.is_shown = False
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

    def is_inner(self):
        return self.type == "inner"

    def is_zone(self):
        return self.type in ["zone", "auto zone", "inner"]

    def is_ruler(self):
        return self.type == "ruler"

    def is_passthrough_zone(self):
        return self.pass_through

    def remove_page(self, pagenum):
        if pagenum in self.pages.keys():
            del self.pages[pagenum]

    def remove_pages(self):
        self.pages = {}

    def destroy(self):
        print "widget destruction"

    def delete(self):
        return self.delete_func(self)

    def can_be_removed(self):
        return self.pages == {}

    def geometry(self):
        x, y = self.pos
        return ([x, x + self.WIDTH], [y, y + self.HEIGHT])

    def contains(self, point_tuple):
        x, y = point_tuple
        x_range, y_range = self.geometry()
        return x in x_range and y in y_range

    def intersects(self, rect_tuple):
        x1, y1, x2, y2 = rect_tuple
        width = x2 - x1
        height = y2 - y1
        x_range, y_range = self.geometry()
        x_topleft, y_topleft = x_range[0], y_range[0]
        x_bottomleft, y_bottomleft = x_range[0], y_range[1]
        x_topright, y_topright = x_range[1], y_range[0]
        x_bottomright, y_bottomright = x_range[1], y_range[1]
        return not(x2 < x_topleft or x1 > x_topright or \
                   y2 < y_topleft or y1 > y_bottomright)


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
        if mark.auto:
            mark.type = "auto zone"
        elif mark.inner:
            mark.type = "inner"
        else:
            mark.type = "zone"
        return mark


# figure out that cas-xml is loaded and parsed properly
class BookControllerTest(unittest.TestCase):

    def _fill_with_data(self):
        start_data = {"pos": (0, 10),
                      "parent": "MockParent",
                      "cas_id": "lesson:bla-bla-bla",
                      "page": 5,
                      "delete_func": self.controller.delete_funcs["start_end"],
                      "name": "lesson blablabla. Paragraph 2",
                      "type": "start"}
        end_data = {"pos": (0, 190),
                    "parent": "MockParent",
                    "cas_id": "lesson:bla-bla-bla",
                    "page": 25,
                    "delete_func": self.controller.delete_funcs["start_end"],
                    "name": "lesson blablabla. Paragraph 2",
                    "type": "end"}
        self.controller.add_mark(start_data)
        self.controller.add_mark(end_data)
        ruler_data = {"pos": (4, 80),
                      "parent": "MockParent",
                      "name": u"",
                      "delete_func": self.controller.delete_funcs["ruler"],
                      "type": "horizontal"}
        self.controller.add_ruler(ruler_data)
        # now place zone manually
        zone_data = {"pos": (55, 50),
                     "parent": "MockParent",
                     "cas_id": "lesson:bla-bla-bla",
                     "zone_id": "01int",
                     "page": 14,
                     "delete_func": self.controller.delete_funcs["zone"],
                     "objects":[ {"oid": "195-12-01-01-int",
                                  "block-id": "some block id"}],
                     "number": "01",
                     "rubric": "int",
                     "margin": "l"}
        # TODO perhaps it's better to test _create_mark_on_click func but it
        # requires a whole deal of new mock objects so here base add method
        # will be tested
        self.controller.add_zone(zone_data)
        self.controller.autozones("MockParent")

    def setUp(self):
        super(BookControllerTest, self).setUp()
        self.markup_file = "tests/native-test.xml"
        self.display_name = "Chemistry-8 course"
        self.pdf_file = "tests/chemistry8.pdf"
        self.cqm = CmsQueryModule(u"tests/config-test")
        self.mc = MockMarkCreator()
        self.toc_controller = MockTocController()
        self.controller = BookController(toc_controller=self.toc_controller,
                                         cqm=self.cqm,
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
        # try to add duplicate start mark, make sure that nothing has changed
        d_start = self.controller.add_mark(start_data)
        self.assertEqual(d_start, None)
        self.assertEqual(self.controller.paragraph_marks[start.cas_id],
                         {"marks": (start, None), "zones": []})
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

        # here come autozones tests
        placed = self.controller.autozones("MockParent")
        # get auto added zones, passthrough and plain ones
        ptz = next((z for z in self.\
                    controller.paragraph_marks["lesson:bla-bla-bla"]["zones"] \
                    if z.pass_through), None)
        auto_con = next((z for z in self.\
                    controller.paragraph_marks["lesson:bla-bla-bla"]["zones"] \
                    if z.zone_id=="con"), None)
        self.assertEquals(placed, 2)
        self.assertFalse(ptz==None)
        self.assertFalse(auto_con==None)
        # have to be as close to start\end as possible
        self.assertEqual(ptz.page, 5)
        self.assertEqual(auto_con.page, 25)
        for p in range(12, 26):
            self.assertTrue(p in self.controller.paragraphs)
            self.assertTrue(p in ptz.pages)
            if p == end.page:
                # check that zone.y() < end.y()
                self.assertTrue(ptz.y() < end.y())
                self.assertEqual(self.controller.paragraphs[p]["zones"],
                                 [ptz, auto_con])
            else:
                self.assertFalse(
                    auto_con in self.controller.paragraphs[p]["zones"])
                self.assertEqual(self.controller.paragraphs[p]["zones"],
                                 [ptz])
        # now place zone manually
        zone_data = {"pos": (55, 50),
                     "parent": "MockParent",
                     "cas_id": "lesson:bla-bla-bla",
                     "zone_id": "01int",
                     "page": 14,
                     "delete_func": lambda x: x,
                     "objects":[ {"oid": "195-12-01-01-int",
                                  "block-id": "some block id"}],
                     "number": "01",
                     "rubric": "int",
                     "margin": "l"}
        # TODO perhaps it's better to test _create_mark_on_click func but it
        # requires a whole deal of new mock objects so here base add method
        # will be tested
        m_zone = self.controller.add_zone(zone_data)
        self.assertTrue(m_zone.page in self.controller.paragraphs)
        self.assertEqual(self.controller.paragraphs[m_zone.page]["zones"],
                         [ptz, m_zone])
        # now make sure that symmetrical structure is normally filled-in
        self.assertEqual(self.controller.paragraph_marks[m_zone.cas_id],
                         {"marks": (start, end),
                          "zones": [ptz, auto_con, m_zone]})
        # check add ruler
        ruler_data = {"pos": (4, 80),
                      "parent": "MockParent",
                      "name": u"",
                      "delete_func": self.controller.delete_funcs["ruler"],
                      "type": "horizontal"}
        ruler = self.controller.add_ruler(ruler_data)
        self.assertTrue(ruler in self.controller.get_rulers())

    def test_delete_marks(self):
        # TODO here deletion from main controller structures, paragraphs and
        # paragraph_marks will be tested
        self._fill_with_data()
        zones = self.controller.paragraph_marks["lesson:bla-bla-bla"]["zones"]
        self.assertEqual(len(zones), 3)
        # manually placed
        self.assertEqual(zones[0].page, 14)
        # auto passthrough bound to start
        self.assertEqual(zones[1].page, 5)
        # auto bound to end
        self.assertEqual(zones[2].page, 25)
        # all but some passthrough zones should be deleted
        self.controller.delete_marks(forced=False, marks=zones)
        zones_left = self.controller.\
            paragraph_marks["lesson:bla-bla-bla"]["zones"]
        self.assertEqual(len(zones_left), 1)
        # verify all deleted in paragraphs
        self.assertTrue(zones_left[0].pass_through)
        for p in [5, 14, 25]:
            self.assertEqual(self.controller.paragraphs[p]["zones"],
                             zones_left)
        # now delete with forced
        self.controller.delete_marks(forced=True, marks=zones_left)
        # verify all deleted in paragraphs
        for p in [5, 14, 25]:
            self.assertEqual(self.controller.paragraphs[p]["zones"], [])
        self._fill_with_data()
        # now test delete all
        self.controller.delete_all()
        self.assertEqual(self.controller.paragraphs, {})
        self.assertEqual(self.controller.paragraph_marks, {})

    def test_verify_functions(self):
        # here verify error functions will be tested
        bad_start = {"pos": (0, 300),
                     "parent": "MockParent",
                     "cas_id": "lesson:bla-bla-bla",
                     "page": 5,
                     "delete_func": self.controller.delete_funcs["start_end"],
                     "name": "lesson blablabla. Paragraph 2",
                     "type": "start"}
        bad_end = {"pos": (0, 190),
                   "parent": "MockParent",
                   "cas_id": "lesson:bla-bla-bla",
                   "page": 5,
                   "delete_func": self.controller.delete_funcs["start_end"],
                   "name": "lesson blablabla. Paragraph 2",
                   "type": "end"}
        start = self.controller.add_mark(bad_start)
        end = self.controller.add_mark(bad_end)
        # end comes before start on same page
        self.assertFalse(self.controller.verify_start_end(start, end))
        bad_start = {"pos": (0, 100),
                     "parent": "MockParent",
                     "cas_id": "lesson:bla-bla-bla2",
                     "page": 15,
                     "delete_func": self.controller.delete_funcs["start_end"],
                     "name": "lesson blablabla. Paragraph 4",
                     "type": "start"}
        bad_end = {"pos": (0, 190),
                   "parent": "MockParent",
                   "cas_id": "lesson:bla-bla-bla2",
                   "page": 5,
                   "delete_func": self.controller.delete_funcs["start_end"],
                   "name": "lesson blablabla. Paragraph 4",
                   "type": "end"}
        start = self.controller.add_mark(bad_start)
        end = self.controller.add_mark(bad_end)
        # end page comes before start page
        self.assertFalse(self.controller.verify_start_end(start, end))
        self.controller.delete_all()
        # normal order
        start_data = {"pos": (0, 10),
                      "parent": "MockParent",
                      "cas_id": "lesson:bla-bla-bla",
                      "page": 5,
                      "delete_func": self.controller.delete_funcs["start_end"],
                      "name": "lesson blablabla. Paragraph 2",
                      "type": "start"}
        end_data = {"pos": (0, 190),
                    "parent": "MockParent",
                    "cas_id": "lesson:bla-bla-bla",
                    "page": 25,
                    "delete_func": self.controller.delete_funcs["start_end"],
                    "name": "lesson blablabla. Paragraph 2",
                    "type": "end"}
        start = self.controller.add_mark(start_data)
        end = self.controller.add_mark(end_data)
        self.assertTrue(self.controller.verify_start_end(start, end))
        # check both start\end
        self.assertTrue(self.controller.verify_mark_pairs())
        # at the moment have start and end in normal order, let's delete one
        self.controller.delete_marks(marks = [start])
        self.assertFalse(self.controller.verify_mark_pairs())
        # when both ends are deleted should get no error (not erroneous, but
        # default, markless state)
        self.controller.delete_marks(marks = [end])
        self.assertTrue(self.controller.verify_mark_pairs())
        # brackets error (appears when start of some paragraph is in-between
        # some other paragraph whereas end lays outside that other paragraph)
        self.controller.delete_all()
        start_data = {"pos": (0, 10),
                      "parent": "MockParent",
                      "cas_id": "lesson:bla-bla-bla",
                      "page": 5,
                      "delete_func": self.controller.delete_funcs["start_end"],
                      "name": "lesson blablabla. Paragraph 2",
                      "type": "start"}
        end_data = {"pos": (0, 190),
                    "parent": "MockParent",
                    "cas_id": "lesson:bla-bla-bla",
                    "page": 25,
                    "delete_func": self.controller.delete_funcs["start_end"],
                    "name": "lesson blablabla. Paragraph 2",
                    "type": "end"}
        start = self.controller.add_mark(start_data)
        end = self.controller.add_mark(end_data)
        # by now everything is ok
        self.assertTupleEqual(self.controller.verify_brackets(), (True, None))
        bad_start = {"pos": (0, 10),
                     "parent": "MockParent",
                     "cas_id": "lesson:fffuuuuu",
                     "page": 6,
                     "delete_func": self.controller.delete_funcs["start_end"],
                     "name": "lesson blablabla. Paragraph 2",
                     "type": "start"}
        bad_end = {"pos": (0, 10),
                   "parent": "MockParent",
                   "cas_id": "lesson:fffuuuuu",
                   "page": 14,
                   "delete_func": self.controller.delete_funcs["start_end"],
                   "name": "lesson blablabla. Paragraph 2",
                   "type": "start"}
        bad_s = self.controller.add_mark(bad_start)
        bad_e = self.controller.add_mark(bad_end)
        # TODO perhaps it's not correct to return end of wrongly placed
        # paragraph, but will leave it as is at least now
        self.assertTupleEqual(self.controller.verify_brackets(),
                              (False, end))

    def test_go_to_page(self):
        # test show\hide marks functionality here as well
        self._fill_with_data()
        self.controller.go_to_page(6)
        self.assertEqual(self.controller.pagenum, 6)
        # make sure that no marks other than those that should be on page 6 are
        # shown.
        # Section mode -> only start\end and rulers;
        # Markup mode -> start\end and marks, no rulers
        self.controller.set_normal_section_mode()
        self.assertTrue(self.controller.is_section_mode())
        # make sure that all rulers are visible regardless of page we are on
        self.assertTrue(all(r.is_shown for r in self.controller.rulers))
        # in sections mode all start\end marks shown
        self.assertTrue(all(m.is_shown for m in
                            self.controller.paragraphs[6]["marks"]))
        # no zones in sections mode
        self.assertTrue(all(not z.is_shown for z in
                            self.controller.paragraphs[6]["zones"]))
        self.controller.go_to_page(25)
        mark = self.controller.find_any_at_point((2, 199))
        self.assertTrue(mark.is_end())
        # in markup mode start\end + zones, no rulers
        self.controller.set_normal_markup_mode()
        self.assertTrue(self.controller.is_markup_mode())
        self.assertTrue(all(m.is_shown for m in
                            self.controller.paragraphs[7]["marks"]))
        self.assertTrue(all(z.is_shown for z in
                            self.controller.paragraphs[7]["zones"]))
        self.assertTrue(all(not r.is_shown for r in self.controller.rulers))
        # check that no start\end can be found and so modified
        self.controller.go_to_page(5)
        mark = self.controller.find_any_at_point((2, 11))
        self.assertTrue(mark.is_zone())

    def test_find_and_viewport_functions(self):
        # first test find_at_point functions
        self._fill_with_data()
        marks = self.controller.paragraph_marks["lesson:bla-bla-bla"]["marks"]
        start = next((m for m in marks if m.is_start()), None)
        # exact match
        elem = self.controller.find_at_point((0, 10), marks)
        self.assertEqual(elem, start)
        # non exact match
        elem = self.controller.find_at_point((2, 16), marks)
        self.assertEqual(elem, start)
        # test viewport match func
        self.assertTrue(self.controller.is_section_mode())
        in_viewport = self.controller.is_in_viewport((8, 30),
                                                     "lesson:bla-bla-bla")
        # start\end marks can be placed anywhere
        self.assertTrue(in_viewport)
        self.controller.set_normal_markup_mode()
        self.assertTrue(self.controller.is_markup_mode())
        self.controller.go_to_page(6)
        self.assertEqual(self.controller.pagenum, 6)
        self.assertTrue(self.controller.is_in_viewport((8, 30),
                                                       "lesson:bla-bla-bla"))
        self.controller.go_to_page(2)
        # have no marks here, should not be able to put any
        self.assertFalse(self.controller.is_in_viewport((8, 30),
                                                        "lesson:bla-bla-bla"))
        self.controller.go_to_page(25)
        # try to place zone mark after end of paragraph and fail
        self.assertFalse(self.controller.is_in_viewport((8, 300),
                                                        "lesson:bla-bla-bla"))

    # Below high level functions' logic will be tested
    def test_mark_creation_on_click(self):
        self.toc_controller.select("lesson:bla-bla-bla")
        self.assertTrue(self.controller.is_section_mode())
        start = self.controller._create_mark_on_click((16, 5), "MockParent")
        self.assertTrue(start.is_start())
        end = self.controller._create_mark_on_click((34, 80), "MockParent")
        self.assertTrue(end.is_end())
        # try to create start\end again, should be unable to do this
        nomark = self.controller._create_mark_on_click((34, 80), "MockParent")
        self.assertTrue(nomark == None)
        # create ruler
        self.controller.set_vertical_ruler_mode()
        ruler = self.controller._create_mark_on_click((50, 40), "MockParent")
        self.assertTrue(ruler.is_ruler())
        self.controller.set_normal_markup_mode()
        self.assertTrue(self.controller.is_markup_mode())
        self.toc_controller.select(
            "lesson:bla-bla-bla", "01pic", ["obj1", "obj2"], pdf_rubric="pic")
        zone = self.controller._create_mark_on_click((46, 51), "MockParent")
        self.assertTrue(zone.is_zone())
        self.assertTrue(zone in self.controller.paragraphs[zone.page]["zones"])
        # now try to place the same zone again, shoul fail
        zone = self.controller._create_mark_on_click((0, 45), "MockParent")
        self.assertTrue(zone == None)
        # inner zone
        self.toc_controller.select(
            "lesson:bla-bla-bla", "09pic", ["obj1"], pdf_rubric="pic",
            inner=True)
        inner_zone = self.controller._create_mark_on_click((46, 51),
                                                          "MockParent")
        self.assertTrue(inner_zone is not None)
        self.assertTrue(inner_zone.is_inner())


if __name__ == '__main__':
    unittest.main()
