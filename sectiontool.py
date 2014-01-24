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
                line.split('=', 2)[1].strip('\"\' \n') for line in f.readlines()
            }
        if 'url' not in self.config_data.keys() or \
                'resolve_url' not in self.config_data.keys():
            raise SectionToolError(
                "Base cms url and resolve-url must be set in config!")

    # returns a list of {name, cas-id} in order of appearance in TOC
    def get_cms_course_toc(self, course_id):
        course_url = self.config_data['url'].rstrip('/') + '/' + course_id
        storage = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, course_url)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.setopt(pycurl.USERPWD, self.config_data['user'])
        c.perform()
        if c.getinfo(pycurl.HTTP_CODE) == 200:
            TOC_XPATH = "/is:course/is:lessons/is:lesson/@name"
            tree = etree.fromstring(storage.getvalue())
            lesson_ids = tree.xpath(TOC_XPATH,
                                    namespaces = {"is" : XHTML_NAMESPACE})
            # resolve names
            ids_to_resolve = [ "lesson:" + lesson_id \
                                 for lesson_id in lesson_ids]
            headers = {"Content-type" : "application/json; charset=UTF-8"}
            # TODO move to config
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
            return [{"name": resolved[lesson_id], "cas-id": lesson_id} \
                    for lesson_id in ids_to_resolve]
        else:
            raise SectionToolError("Check your url and user\password settings")
        c.close()


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
        if len(sys.argv) < 2:
            raise LoaderError("Pdf-file name should come as 1st param")
        filename = sys.argv[1]
        maxwidth = get_value("--width", sys.argv)
        maxheight = get_value("--height", sys.argv)
        save_dir = get_value("--savedir", sys.argv) or '.'
        return (filename, maxwidth, maxheight, save_dir)

    filename, width, height, save_dir = parse_args()
    st = SectionTool("config")
    toc = st.get_cms_course_toc('course:279feb39-aa65-4f2a-b42d-6da8a180ea44')
    for elem in toc:
        print elem["name"]

    # show window
    app = QtGui.QApplication(sys.argv)
    ui_mw = BookViewerWidget(DocumentProcessor(filename))
    ui_mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
