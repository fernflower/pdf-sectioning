import pycurl
import sys
from PyQt4 import QtGui, QtCore
from json import dumps, loads
from httplib2 import Http
from StringIO import StringIO
from lxml import etree
from lxml.builder import ElementMaker
from bookviewerwidget import BookViewerWidget
from documentprocessor import DocumentProcessor, LoaderError
from bookcontroller import BookController

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

    def _fetch_data(self, url):
        storage = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.setopt(pycurl.USERPWD,
                 self.config_data['username'] + ":" + \
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
            return [{"name": resolved[lesson_id], "cas-id": lesson_id,
                     "objects": self.get_lesson_objects(lesson_id)} \
                    for lesson_id in ids_to_resolve]
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
            return [{"oid": p.get("objectid"), "block-id": p.get("id"),
                     "rubric": p.get("erubric")}
                    for p in paragraphs]
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
        maxwidth = get_value("--width", sys.argv)
        maxheight = get_value("--height", sys.argv)
        save_dir = get_value("--savedir", sys.argv) or '.'
        return (filename, maxwidth, maxheight, save_dir)

    filename, width, height, save_dir = parse_args()
    st = SectionTool("config")
    toc = st.get_cms_course_toc()

    # show window
    app = QtGui.QApplication(sys.argv)
    # if no filename given: construct controller without docprocessor
    dp = DocumentProcessor(filename) if filename else None
    controller = BookController(toc, dp)
    ui_mw = BookViewerWidget(controller)
    ui_mw.show()
    if not dp:
        ui_mw.open_file()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
