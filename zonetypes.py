#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from PyQt4 import QtGui


DEFAULT_ZONE_TYPES = ["dic", "tra", "con"]

# autozones that must be placed near the start of the page in the order given
START_AUTOZONES = ["dic"]

# autozones that must be placed at the end of the page in the order given
END_AUTOZONES = ["tra", "con"]

# zones that shoukd appear on every page in paragraph
PASS_THROUGH_ZONES = ["dic"]

MARGINS = ["l", "r", "lr"]


class ZoneIconsProducer(object):
    def __init__(self, zones):
        self.zone_types = zones
        self.mock_icon = QtGui.QImage("buttons/Icons/missing.png")
        self.zone_icons = {}

        for zone_type in zones:
            icon_file = "buttons/Icons/icon_%s.png" % zone_type
            self.zone_icons[zone_type] = QtGui.QImage(icon_file) \
                if os.path.isfile(icon_file) else self.mock_icon
        print self.zone_icons

    # TODO later this will be changed as strict validation appears
    def get(self, key):
        if key in self.zone_types:
            return self.zone_icons[key]
        # return a mock object for unfinished types
        else:
            print "Warning: unknown zone type '%s'" % key
            return self.mock_icon
