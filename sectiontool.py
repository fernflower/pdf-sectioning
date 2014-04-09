# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui
from bookviewerwidget import BookViewerWidget
from bookcontroller import BookController
from toccontroller import TocController
from cmsquerymodule import CmsQueryModule


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

    # show window
    app = QtGui.QApplication(sys.argv)
    toc_controller = TocController([], cqm.config_data["start-autozones"],
                                   cqm.config_data["end-autozones"])
    # here display name must be passed in order to create DP later
    controller = BookController(toc_controller, cqm, filename)
    ui_mw = BookViewerWidget(controller, toc_controller)
    ui_mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
