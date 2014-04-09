#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pycurl
import urllib
import os
import json
from json import dumps, loads
from httplib2 import Http
from StringIO import StringIO
from lxml import etree
from lxml.builder import ElementMaker
from zonetypes import DEFAULT_ZONE_TYPES, PASS_THROUGH_ZONES, START_AUTOZONES, \
    END_AUTOZONES

XHTML_NAMESPACE = "http://internet-school.ru/abc"
NSMAP = {'is': XHTML_NAMESPACE}
E = ElementMaker(namespace=XHTML_NAMESPACE, nsmap=NSMAP)


class CmsQueryError(Exception):
    pass


class CmsQueryCanceledByUser(Exception):
    pass


class CmsQueryModule(object):
    DEFAULT_CONFIG = "config"

    def __init__(self, config_filename=None):
        self.config_data = {}
        self.parse_config(config_filename or self.DEFAULT_CONFIG)
        self.display_name = None

    @property
    def any_course_data(self):
        return "cms-course" in self.config_data

    def parse_config(self, config_filename):
        with open(config_filename) as f:
            self.config_data = {
                line.split('=', 2)[0].strip(' \"\''):
                    line.split('=', 2)[1].strip('\"\' \n')
                for line in f.readlines() if not
                (line.strip().startswith('#') or line.strip() == "")
            }
        if any(map(lambda param: param not in self.config_data.keys(),
                   ['url', 'resolve-url', 'ping-url', 'search-url'])):
            raise CmsQueryError(
                "Some vital urls are missing in default config!!!")

        # !!TODO no login\password data stored in config in production version!
        for key in self._defaults:
            if key not in ["login", "password"]:
                self.config_data[key] = self._defaults[key]

    @property
    def _defaults(self):
        return {'passthrough-zones': PASS_THROUGH_ZONES,
                'start-autozones': START_AUTOZONES,
                'end-autozones': END_AUTOZONES,
                'zonetypes': DEFAULT_ZONE_TYPES,
                'all-autozones': START_AUTOZONES + END_AUTOZONES,
                'margins': ['l, r'],
                'margin-width': 50,
                'zone-width': 20,
                'first-page': 'l',
                'login': u'',
                'password': u''}

    def _fetch_data(self, url, login, password):
        # for some alternatively talented people who have russian
        # usernames\passwords (everything might happen)
        login = login.encode('utf-8')
        password = password.encode('utf-8')
        storage = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.USERPWD, login + ":" + password)
        # TODO find out how to use certificate
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
        data = None
        if code == 200:
            data = storage.getvalue()
        c.close()
        return (code, data)

    def validate_user_data(self, login, password):
        url = self.config_data['ping-url'].rstrip('/')
        code, data = self._fetch_data(url, login, password)
        return code == 200

    def search_for_course(self, name_part, login, password):
        if not self.validate_user_data(login, password):
            return []
        url = self.config_data['search-url'] + "?" + \
            "name_filter={}&labels=course&excluded_names=&sort=name".\
            format(urllib.quote(name_part.encode('utf-8')))
        code, data = self._fetch_data(url, login, password)
        if not data:
            return []
        data = json.loads(data)
        return [(elem["display_name"], urllib.unquote(elem["encoded_name"]))
                for elem in data["documents"]]

    # retrieve available zonetypes from ebook-defs
    def get_zone_types(self, login, password):
        defs_url = self.config_data['url'].rstrip('/') + '/object:ebook-defs'
        code, data = self._fetch_data(defs_url, login, password)
        all_zones = []
        if data:
            TYPE_XPATH = "/is:object/is:text/is:rubric-def/@oid-suffix"
            all_zones = etree.fromstring(data).\
                xpath(TYPE_XPATH, namespaces=NSMAP)
        if not data or all_zones == []:
            return self._defaults["zonetypes"]
        else:
            return all_zones

    # returns a list of {name, cas-id} in order of appearance in TOC
    def get_cms_course_toc(self, login, password, course_id=None, progress=None):
        if not self.any_course_data and not course_id:
            return []
        course_id = course_id or self.config_data['cms-course']
        course_url = os.path.join(self.config_data['url'],
                                  course_id.encode('utf-8'))
        code, data = self._fetch_data(course_url, login, password)
        if data:
            if progress:
                progress.setLabelText(u"Загрузка курса из cms...")
            TOC_XPATH = "/is:course/is:lessons/is:lesson/@name"
            tree = etree.fromstring(data)
            self.display_name = tree.xpath(
                "/is:course/@display-name", namespaces=NSMAP)[0]
            lesson_ids = tree.xpath(TOC_XPATH, namespaces=NSMAP)
            # resolve names
            ids_to_resolve = ["lesson:" + lesson_id
                              for lesson_id in lesson_ids]
            headers = {"Content-type": "application/json; charset=UTF-8"}
            body = dumps(ids_to_resolve)
            http_obj = Http()
            http_obj.add_credentials(self.config_data['login'],
                                     self.config_data['password'])
            resp, content = http_obj.request(
                uri=self.config_data["resolve-url"], method='POST',
                headers=headers,
                body=body)
            if resp.status != 200:
                raise CmsQueryError("Could not resolve lesson names!")
            resolved = loads(content)
            toc = []
            if progress:
                progress.setRange(0, len(ids_to_resolve))
            for i, lesson_id in enumerate(ids_to_resolve):
                if progress:
                    progress.setValue(i)
                    if progress.wasCanceled():
                        progress.close()
                        raise CmsQueryCanceledByUser()
                toc.append(
                    {"name": resolved[lesson_id],
                     "cas-id": lesson_id,
                     "objects": self._get_lesson_objects(
                         lesson_id, login, password)})
            auto_types = self._get_autozone_types(toc)
            return (toc, auto_types)
        else:
            raise CmsQueryError("Check your url and user\password settings")

    def _get_autozone_types(self, toc):
        result = set()

        def _get_autozone_type(oid):
            parts = oid.split('-')
            zone_type = parts[4] if len(parts) > 4 else None
            if zone_type and parts[2] == "00":
                return zone_type
            return None
        for para in toc:
            for zt in para["objects"]:
                zone_type = _get_autozone_type(zt["oid"])
                if zone_type:
                    result.add(zone_type)
        return list(result)

    def _get_lesson_objects(self, lesson_id, login, password):
        lesson_url = os.path.join(self.config_data['url'], lesson_id)
        code, data = self._fetch_data(lesson_url, login, password)
        if data:
            PARAGRAPHS_XPATH = "/is:lesson/is:content/is:paragraph | /is:lesson/is:content/is:test"
            tree = etree.fromstring(data)
            paragraphs = tree.xpath(PARAGRAPHS_XPATH, namespaces=NSMAP)
            objects = [{"oid": p.get("objectid"),
                        "block-id": p.get("id"),
                        "rubric": p.get("erubric"),
                        "name": p.xpath("is:name/text()", namespaces=NSMAP)[0]
                        } for p in paragraphs]
            return objects
        else:
            raise CmsQueryError("Could not get lesson's {} object list!".
                                format(lesson_id))
