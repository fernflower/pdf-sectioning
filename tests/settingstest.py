# -*- coding: utf-8 -*-
import unittest
from PyQt4 import QtGui
from settings import Settings
from bookcontroller import BookController
from toccontrollertest import MockTocController
from sectiontool import CmsQueryModule


class SettingsTest(unittest.TestCase):
    def setUp(self):
        super(SettingsTest, self).setUp()
        self.app = QtGui.QApplication([])
        self.markup_file = "tests/native-test.xml"
        self.display_name = "Chemistry-8 course"
        self.pdf_file = "tests/chemistry8.pdf"
        self.cqm = CmsQueryModule(u"tests/config-test")
        #self.mc = MockMarkCreator()
        self.toc_controller = MockTocController()
        self.controller = BookController(toc_controller=self.toc_controller,
                                         cqm=self.cqm,
                                         filename=self.pdf_file,
                                         mark_creator=None)

    def test_config_parse(self):
        settings = Settings(controller=self.controller, parent=None)
