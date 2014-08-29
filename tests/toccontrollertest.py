# -*- coding: utf-8 -*-
import unittest
import json
from PyQt4 import QtGui
from tocelem import QObjectElem, QZone, QTocElem, QMarkerTocElem
from cmsquerymodule import CmsQueryModule


class MockTocElem(object):
    def __init__(self, cas_id, zone_id, objects, **kwargs):
        self.cas_id = cas_id
        self.name = "mock toc %s" % cas_id
        self.zone_id = zone_id
        self.objects = objects
        self.number = kwargs.get("number") or "no_number"
        self.pdf_rubric = kwargs.get("pdf_rubric") or "no_rubric"
        self.is_inner = kwargs.get("inner") or False

    def objects_as_dictslist(self):
        return self.objects


class MockTocController(object):
    def __init__(self):
        self.active_elem = None

    @property
    def is_anything_selected(self):
        return self.active_elem is not None

    @property
    def is_zone_selected(self):
        return self.is_anything_selected and \
            self.active_elem.zone_id is not None

    def get_elem(self, cas_id, mode):
        return None

    def set_state(self, value, cas_id, is_ok=False, braces_err=False):
        pass

    def set_default_state(self, cas_id):
        pass

    def process_zone_added(self, zone):
        print "%s has been added" % zone.name

    def get_autoplaced_zones(self, cas_id, icons_producer=None):
        return [{"type": "repeat",
                 "rel-start": 0,
                 "rel-end": None,
                 "rubric": "dic",
                 "zone-id": "dic",
                 "page": 12,
                 "objects":[ {"oid": "195-12-01-01-int",
                              "block-id": "some block id"} ] },
                {"type": "single",
                 "rel-start": None,
                 "rel-end": -20,
                 "rubric": "con",
                 "zone-id": "con",
                 "page": 15,
                 "objects": [{"oid": "195-15-00-01-con",
                              "block-id": "qqqq"}]}]

    def process_zone_deleted(self, zone):
        print "%s has been deleted" % zone.name

    # not present in real Toc Controller, but useful for testing
    def select(self, cas_id, zone_id=None, objects=None, **kwargs):
        self.active_elem = MockTocElem(cas_id, zone_id, objects, **kwargs)

    def reload_course(self, course_id, start, end):
        print("Course {} reloaded").format(course_id)

class TocControllerTest(unittest.TestCase):
    def setUp(self):
        super(TocControllerTest, self).setUp()
        self.defaults = CmsQueryModule(u"tests/config-test")._defaults
        self.course_data_file = u"tests/course-data"

    def _get_course_data(self):
        return [json.loads(l) for l in
                open(self.course_data_file).readlines()]

    def test_tocelems_creation(self):
        # necessary to test qzone\qautozonecontainer without mock objects
        self.app = QtGui.QApplication([])
        # elements representing objects in views, unmodifiable
        obj1 = QObjectElem("195-12-01-01-int", "some block id", "int",
                           "Walter White")
        self.assertFalse(obj1.isSelectable())
        self.assertFalse(obj1.isEditable())
        self.assertEqual(obj1.display_name, "Walter White\n(195-12-01-01-int)")
        self.assertEqual(obj1.zone_id, "01int")
        self.assertFalse(obj1.is_inner)
        self.assertFalse(obj1.is_autoplaced)
        obj_auto = QObjectElem("195-12-00-04-dic", "some block id", "dic")
        # no name given
        self.assertEqual(obj_auto.display_name, "195-12-00-04-dic")
        self.assertTrue(obj_auto.is_autoplaced)
        self.assertFalse(obj_auto.is_inner)
        obj_inner = QObjectElem("195-12-01-innerpic", "some block id", "pic",
                                "Inner image")
        self.assertTrue(obj_inner.is_inner)
        self.assertFalse(obj_inner.is_autoplaced)
        # objects representing zones. Have to be selectable and unmodifiable
        zone = QZone(None, "interest", [obj1])
        self.assertTrue(zone.isSelectable())
        self.assertFalse(zone.isEditable())
        self.assertEqual(zone.pdf_rubric, "int")
        self.assertTrue(zone.is_on_page(12))
        self.assertFalse(zone.is_autoplaced)
        self.assertEqual(zone.zone_id, "01int")
        self.assertFalse(zone.is_inner)
        zone_auto = QZone(None, "dic", [obj_auto])
        self.assertTrue(zone_auto.is_autoplaced)
        self.assertEqual(zone_auto.zone_id, "dic")
        # construct one elem of every kind: SectionToc and MarkupToc
        para_data = {"objects":
                       [ {"block-id": "6c13e284-c3e0-48d3-92ac-d37955cec4d1",
                          "oid": "195-012-00-01-dic",
                          "rubric": "dict",
                          "name": "\u041b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f"},
                        {"block-id": "916a3866-456f-4e2f-ab08-6bbb4a2a6445",
                         "oid": "195-012-00-02-dic",
                         "rubric": "dict",
                         "name": "\u042d\u043a\u0441\u043f\u0435\u0440\u0438\u043c\u0435\u043d\u0442"},
                        {"block-id": "8942fc28-20d7-47ea-974f-c66085007ee7",
                         "oid": "195-012-01-01-pic",
                         "rubric": "figure",
                         "name": "\u041a\u043e\u043b\u0431\u044b \u042d\u0440\u043b\u0435\u043d\u043c\u0435\u0439\u0435\u0440\u0430"},
                        {"block-id": "4c30e710-a37f-4ea8-bdcb-0082d1ce7010",
                         "oid": "195-012-01-innerpic",
                         "rubric": "figure",
                         "name": "I am an inner pic"},
                        {"block-id": "0507cb20-917a-4fad-908f-da493de95547",
                         "oid": "195-013-00-01-tra",
                         "rubric": "train",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u0422\u0440\u0435\u043d\u0430\u0436\u0451\u0440\u00a01"},
                        {"block-id": "6acaa242-4623-411e-9d41-26bdab36b780",
                         "oid": "195-013-00-02-tra",
                         "rubric": "train",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u0422\u0440\u0435\u043d\u0430\u0436\u0451\u0440\u00a02"},
                        {"block-id": "df7b26b5-0693-4879-a8dc-3540afb7f3ba",
                         "oid": "195-013-00-03-tra",
                         "rubric": "train",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u0422\u0440\u0435\u043d\u0430\u0436\u0451\u0440\u00a03"},
                        {"block-id": "9d7b5a44-23b2-4c07-b598-e1e78554ea04",
                         "oid": "195-013-00-01-con",
                         "rubric": "control",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u00a01"},
                        {"block-id": "f6d6c05a-230c-4567-8769-bff324299f62",
                         "oid": "195-013-00-02-con",
                         "rubric": "control",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u00a02"},
                        {"block-id": "5c02230b-e683-466d-893c-f772fde3eaed",
                         "oid": "195-013-00-03-con",
                         "rubric": "control",
                         "name": "\u0425\u0438\u043c\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f. \u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u00a03"}],
                       "name": "Sample paragraph name",
                       "cas-id": "lesson:673cc5f9-d4ad-49f4-b219-41c60b7dd33f"}
        section_toc = QTocElem(para_data["name"], para_data["cas-id"])
        self.assertTrue(section_toc.is_not_started())
        markup_toc = QMarkerTocElem(para_data["name"],
                                    para_data["cas-id"],
                                    para_data["objects"],
                                    self.defaults["start-autozones"],
                                    self.defaults["end-autozones"])
        zone = markup_toc.get_zone("tra")
        self.assertTrue(isinstance(zone, QZone))
        self.assertEqual(zone.cas_id, markup_toc.cas_id)
        self.assertTrue(zone.is_autoplaced)
        self.assertTrue(len(zone.objects) == 3)
        # now test inner zone loading
        inner_zone = markup_toc.get_zone("01innerpic")
        self.assertTrue(inner_zone.is_inner)
        self.assertTrue(len(inner_zone.objects) == 1)
        # test auto zone container (have dic, train and control)
        self.assertEqual(len(markup_toc.auto.zones), 3)
        ## test that finished\unfinished state changes correctly
        for zone in markup_toc.zones:
            zone.set_finished(True)
        self.assertTrue(markup_toc.is_finished())
        self.assertTrue(markup_toc.auto.is_finished())
        markup_toc.auto.zones[0].set_finished(False)
        self.assertFalse(markup_toc.auto.is_finished())
        self.assertFalse(markup_toc.is_finished())
        # now mark it as finished again
        markup_toc.auto.zones[0].set_finished(True)
        self.assertTrue(markup_toc.auto.is_finished())
        self.assertTrue(markup_toc.is_finished())
