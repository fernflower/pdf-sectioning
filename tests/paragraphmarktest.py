# -*- coding: utf-8 -*-
import unittest
from PyQt4 import QtGui
from paragraphmark import make_paragraph_mark, make_ruler_mark, make_zone_mark, \
    QPassThroughZoneMark, QInnerZoneMark, QStartParagraph


class ParagraphMarkTest(unittest.TestCase):
    def setUp(self):
        super(ParagraphMarkTest, self).setUp()

    # binding to ruler has to be tested here as well as ruler deletion when
    # moved outside vieport
    def test_create_and_move(self):
        app = QtGui.QApplication([])
        mock_parent = QtGui.QLabel()
        # start\end can be moved only by y
        start = make_paragraph_mark(pos=(34, 12), parent=mock_parent,
                                    cas_id="lesson:123", page=15,
                                    delete_func=lambda x: x, name="start",
                                    type="start")
        self.assertTrue(isinstance(start, QStartParagraph))
        self.assertEqual(start.pos_as_tuple(), (0, 12))
        start.move((10, 40))
        self.assertEqual(start.pos_as_tuple(), (0, 52))
        # horizontal rulers are moved by y, vertical - by x
        hor_ruler = make_ruler_mark(pos=(23, 65), parent=mock_parent,
                                         delete_func=lambda x: x,
                                         type="horizontal")
        self.assertEqual(hor_ruler.pos_as_tuple(), (0, 65))
        hor_ruler.move((40, -3))
        self.assertEqual(hor_ruler.pos_as_tuple(), (0, 62))
        vert_ruler = make_ruler_mark(pos=(1, 65), parent=mock_parent,
                                          delete_func=lambda x: x,
                                          type="vertical")
        self.assertEqual(vert_ruler.pos_as_tuple(), (1, 0))
        vert_ruler.move((41, 3))
        self.assertEqual(vert_ruler.pos_as_tuple(), (42, 0))
        # not inner zones can be moved only by y
        zone = make_zone_mark(pos=(85, 119), parent=mock_parent,
                              delete_func=lambda x: x,
                              cas_id="lesson:123", zone_id="dic03",
                              page=11, objects=[], rubric="dic",
                              margin="l")
        self.assertEqual(zone.pos_as_tuple(), (0, 119))
        zone.move((14, 14))
        self.assertEqual(zone.pos_as_tuple(), (0, 133))
        # same thing with auto and pass through zones
        pass_zone = make_zone_mark(pos=(85, 119), parent=mock_parent,
                                   delete_func=lambda x: x,
                                   cas_id="lesson:123", zone_id="dic03",
                                   page=11, objects=[], rubric="dic",
                                   margin="l", auto=True, pass_through=True)
        self.assertTrue(isinstance(pass_zone, QPassThroughZoneMark))
        self.assertEqual(pass_zone.pos_as_tuple(), (0, 119))
        pass_zone.move((14, 14))
        self.assertEqual(pass_zone.pos_as_tuple(), (0, 133))
        # inner zones can be moved both by x and by y
        inner_zone = make_zone_mark(pos=(85, 119), parent=mock_parent,
                                    delete_func=lambda x: x,
                                    cas_id="lesson:123", zone_id="dic03",
                                    page=11, objects=[], rubric="dic",
                                    margin="l", inner=True, pass_through=True)
        self.assertTrue(isinstance(inner_zone, QInnerZoneMark))
        self.assertTrue(inner_zone.should_show(11))
        self.assertEqual(inner_zone.pos_as_tuple(), (85, 119))
        inner_zone.move((14, 14))
        self.assertEqual(inner_zone.pos_as_tuple(), (99, 133))
        # now test correct self-identification
        self.assertTrue(zone.is_zone())
        self.assertTrue(inner_zone.is_zone())
        self.assertTrue(inner_zone.is_inner_zone())
        self.assertTrue(start.is_start())
        self.assertTrue(pass_zone.is_passthrough_zone())
        self.assertTrue(hor_ruler.is_ruler())
