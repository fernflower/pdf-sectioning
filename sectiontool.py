import pycurl
import urllib
import sys
import json
from PyQt4 import QtGui, QtCore
from json import dumps, loads
from httplib2 import Http
from StringIO import StringIO
from lxml import etree
from lxml.builder import ElementMaker
from bookviewerwidget import BookViewerWidget
from bookcontroller import BookController
from toccontroller import TocController
from zonetypes import DEFAULT_ZONE_TYPES, PASS_THROUGH_ZONES, START_AUTOZONES, \
    END_AUTOZONES, MARGINS

XHTML_NAMESPACE = "http://internet-school.ru/abc"
E = ElementMaker(namespace=XHTML_NAMESPACE,
                 nsmap={'is' : XHTML_NAMESPACE})

class CmsQueryError(Exception):
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
                line.split('=', 2)[0].strip(' \"\'') : \
                line.split('=', 2)[1].strip('\"\' \n') \
                for line in f.readlines() if not \
                (line.strip().startswith('#') or line.strip() == "")
            }
        if any(map(lambda param: param not in self.config_data.keys(),
                    ['url', 'resolve-url', 'ping-url', 'search-url'])):
            raise CmsQueryError(
                "Some vital urls are missing in default config!!!")

        def _check_against(key, against):
            return  [e.strip() for e in self.config_data[key].split(',')
                     if e.strip() in against]

        def _set_given_or_dfl(key, value):
            if value != []:
                self.config_data[key] = value
            else:
                self.config_data[key] = self._defaults[key]

        for param in self._defaults.keys():
            if param in self.config_data.keys():
                if param in ['passthrough-zones',
                             'start-autozones', 'end-autozones']:
                    _set_given_or_dfl(param, _check_against(
                        param, DEFAULT_ZONE_TYPES))
                elif param == 'margins':
                    _set_given_or_dfl(param, _check_against(param, MARGINS))
            else:
                # add default value
                self.config_data[param] = self._defaults[param]

    @property
    def _defaults(self):
        return {'passthrough-zones': PASS_THROUGH_ZONES,
                'start-autozones': START_AUTOZONES,
                'end-autozones': END_AUTOZONES,
                'all-zones': DEFAULT_ZONE_TYPES,
                'margins': ['l, r'],
                'margin-width': 50,
                'zone-width': 20,
                'first-page': 'l'}

    def _fetch_data(self, url, login, password):
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
        code, data = self._fetch_data(url, str(login), str(password))
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

    # returns a list of {name, cas-id} in order of appearance in TOC
    def get_cms_course_toc(self, course_id=None):
        if not self.any_course_data and not course_id:
            return []
        course_id = course_id or self.config_data['cms-course']
        course_url = self.config_data['url'].rstrip('/') + '/' + course_id.encode('utf-8')
        login = self.config_data['login']
        password = self.config_data['password']
        code, data = self._fetch_data(course_url, login, password)
        if data:
            TOC_XPATH = "/is:course/is:lessons/is:lesson/@name"
            tree = etree.fromstring(data)
            self.display_name = tree.xpath(
                "/is:course/@display-name",
                namespaces = {"is" : XHTML_NAMESPACE})[0]
            lesson_ids = tree.xpath(TOC_XPATH,
                                    namespaces = {"is" : XHTML_NAMESPACE})
            # resolve names
            ids_to_resolve = ["lesson:" + lesson_id \
                                 for lesson_id in lesson_ids]
            headers = {"Content-type" : "application/json; charset=UTF-8"}
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
            toc = [{"name": resolved[lesson_id], "cas-id": lesson_id,
                    "objects": self._get_lesson_objects(lesson_id, login, password)} \
                   for lesson_id in ids_to_resolve]
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
        lesson_url = self.config_data['url'].rstrip('/') + '/' + lesson_id
        code, data = self._fetch_data(lesson_url, login, password)
        if data:
            PARAGRAPHS_XPATH = "/is:lesson/is:content/is:paragraph | /is:lesson/is:content/is:test"
            tree = etree.fromstring(data)
            paragraphs = tree.xpath(PARAGRAPHS_XPATH,
                                    namespaces = {"is" : XHTML_NAMESPACE})
            objects = [{"oid": p.get("objectid"),
                        "block-id": p.get("id"),
                        "rubric": p.get("erubric"),
                        "name": p.xpath("is:name/text()",
                                        namespaces = {"is" : XHTML_NAMESPACE})[0]
                        } for p in paragraphs]
            return objects
        else:
            raise CmsQueryError("Could not get lesson's {} object list!".\
                                   format(lesson_id))


def main():
    def parse_args():
        def get_value(param_name, args):
            try:
                idx = args.index(param_name)
                args.pop(idx)
                return args[idx]
            except ValueError:
                # no such param
                return None
        filename = None
        if len(sys.argv) >= 2:
            filename = sys.argv[1]
        return filename

    filename = parse_args()
    cqm = CmsQueryModule()
    toc = cqm.get_cms_course_toc()

    # show window
    app = QtGui.QApplication(sys.argv)
    toc_controller = TocController(toc, cqm.config_data["start-autozones"],
                                   cqm.config_data["end-autozones"])
    # here display name must be passed in order to create DP later
    controller = BookController(toc_controller, cqm, filename)
    ui_mw = BookViewerWidget(controller, toc_controller)
    ui_mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
