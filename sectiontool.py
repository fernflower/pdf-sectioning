import pycurl
import sys
from PyQt4 import QtGui, QtCore
from json import dumps, loads
from httplib2 import Http
from StringIO import StringIO
from lxml import etree
from lxml.builder import ElementMaker
from bookviewerwidget import BookViewerWidget
from bookcontroller import BookController
from toccontroller import TocController
from zonetypes import ZONE_TYPES, PASS_THROUGH_ZONES, START_AUTOZONES, \
    END_AUTOZONES, MARGINS

XHTML_NAMESPACE = "http://internet-school.ru/abc"
E = ElementMaker(namespace=XHTML_NAMESPACE,
                 nsmap={'is' : XHTML_NAMESPACE})

class SectionToolError(Exception):
    pass

class SectionTool(object):

    def __init__(self, config_filename):
        self.parse_config(config_filename)

    def parse_config(self, config_filename):
        with open(config_filename) as f:
            self.config_data = {
                line.split('=', 2)[0].strip(' \"\'') : \
                line.split('=', 2)[1].strip('\"\' \n') \
                for line in f.readlines() if not line.startswith('#')
            }
        if 'url' not in self.config_data.keys() or \
                'resolve_url' not in self.config_data.keys():
            raise SectionToolError(
                "Base cms url and resolve-url must be set in config!")
        if 'cms-course' not in self.config_data.keys():
            raise SectionToolError(
            "Cms-course id should be set in config (cms-course field)!")

        # a list of 2+ is returned as a list, but if [a] -> a (single elem) is
        # returned
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
                    _set_given_or_dfl(param, _check_against(param, ZONE_TYPES))
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
                'margins': 'lr',
                'margin-width': 50,
                'zone-width': 20,
                'first-page': 'l'}

    def _fetch_data(self, url):
        storage = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.setopt(pycurl.USERPWD,
                 self.config_data["username"] + ":" + \
                 self.config_data["password"])
        # TODO find out how to use certificate
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
        data = None
        if code == 200:
            data = storage.getvalue()
        c.close()
        return (code, data)

    # returns a list of {name, cas-id} in order of appearance in TOC
    def get_cms_course_toc(self):
        course_id = self.config_data['cms-course']
        course_url = self.config_data['url'].rstrip('/') + '/' + course_id
        code, data = self._fetch_data(course_url)
        if data:
            TOC_XPATH = "/is:course/is:lessons/is:lesson/@name"
            tree = etree.fromstring(data)
            display_name = tree.xpath("/is:course/@display-name",
                                      namespaces = {"is" : XHTML_NAMESPACE})[0]
            lesson_ids = tree.xpath(TOC_XPATH,
                                    namespaces = {"is" : XHTML_NAMESPACE})
            # resolve names
            ids_to_resolve = [ "lesson:" + lesson_id \
                                 for lesson_id in lesson_ids]
            headers = {"Content-type" : "application/json; charset=UTF-8"}
            body = dumps(ids_to_resolve)
            http_obj = Http()
            http_obj.add_credentials(self.config_data['username'],
                                     self.config_data['password'])
            resp, content = http_obj.request(
                uri=self.config_data["resolve_url"], method='POST',
                headers=headers,
                body=body)
            if resp.status != 200:
                raise SectionToolError("Could not resolve lesson names!")
            resolved = loads(content)
            objects =  [{"name": resolved[lesson_id], "cas-id": lesson_id,
                         "objects": self.get_lesson_objects(lesson_id)} \
                        for lesson_id in ids_to_resolve]
            return (objects, display_name)
        else:
            raise SectionToolError("Check your url and user\password settings")

    def get_lesson_objects(self, lesson_id):
        lesson_url = self.config_data['url'].rstrip('/') + '/' + lesson_id
        code, data = self._fetch_data(lesson_url)
        if data:
            PARAGRAPHS_XPATH = "/is:lesson/is:content/is:paragraph | /is:lesson/is:content/is:test"
            tree = etree.fromstring(data)
            paragraphs = tree.xpath(PARAGRAPHS_XPATH,
                                    namespaces = {"is" : XHTML_NAMESPACE})
            return [{"oid": p.get("objectid"),
                     "block-id": p.get("id"),
                     "rubric": p.get("erubric"),
                     "name": p.xpath("is:name/text()",
                                     namespaces = {"is" : XHTML_NAMESPACE})[0]
                     } for p in paragraphs]
        else:
            raise SectionToolError("Could not get lesson's {} object list!".\
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
    st = SectionTool("config")
    toc, display_name = st.get_cms_course_toc()

    # show window
    app = QtGui.QApplication(sys.argv)
    toc_controller = TocController(toc, st.config_data["start-autozones"],
                                   st.config_data["end-autozones"])
    # here display name must be passed in order to create DP later
    controller = BookController(toc_controller, st.config_data,
                                display_name, filename)
    ui_mw = BookViewerWidget(controller, toc_controller)
    ui_mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
