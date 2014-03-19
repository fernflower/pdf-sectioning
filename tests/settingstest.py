# -*- coding: utf-8 -*-
import unittest
from tempfile import NamedTemporaryFile
from bookcontroller import BookController
from toccontrollertest import MockTocController
from sectiontool import CmsQueryModule, CmsQueryError


class SettingsTest(unittest.TestCase):
    def setUp(self):
        super(SettingsTest, self).setUp()
        self.markup_file = "tests/native-test.xml"
        self.display_name = "Chemistry-8 course"
        self.pdf_file = "tests/chemistry8.pdf"
        self.cqm = CmsQueryModule(u"tests/config-test")
        self.toc_controller = MockTocController()
        self.controller = BookController(toc_controller=self.toc_controller,
                                         cqm=self.cqm,
                                         filename=self.pdf_file,
                                         mark_creator=None)

    def test_config_parse(self):
        defaults = self.cqm._defaults
        # no userdata in defaults
        self.assertFalse("password" in defaults)
        self.assertFalse("login" in defaults)
        # resolve url is missing
        config_not_all_urls = u"""
            url = 'https://e-cms.igrade.ru/raw/'
            ping-url = 'https://e-cms.igrade.ru/cms'
            cms-course = course:51aee4ac-1edf-4b2a-8ce6-dd1769c94333
            margins = l, r
            first-page = l
            username = i-vasilevskaja
            passthrough-zones = dic
            start-autozones = dic
            # should be kept somewhere else, but for prototype will do
            password = nope
        """
        with NamedTemporaryFile() as bad_config:
            bad_config.write(config_not_all_urls)
            bad_config.seek(0)
            self.assertRaises(CmsQueryError,
                              lambda: CmsQueryModule(bad_config.name))

        config_only_vital_data = u"""
            url = 'https://e-cms.igrade.ru/raw/'
            ping-url = 'https://e-cms.igrade.ru/cms'
            resolve-url = 'https://e-cms.igrade.ru/edit/resolve'
        """
        with NamedTemporaryFile() as ok_config:
            ok_config.write(config_only_vital_data)
            ok_config.seek(0)
            cqm = CmsQueryModule(ok_config.name)
            # no url data in default
            self.assertTrue(all((lambda key: key not in cqm._defaults,
                                ["url", "ping-url", "resolve-url"])))
            # margins, first page, default sections here though
            self.assertTrue(all((lambda key: key in cqm._defauts,
                                ["margins", "first-page", "start-autozones",
                                 "end-autozones", "passthrough_zones"])))
