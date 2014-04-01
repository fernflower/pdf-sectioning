#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui


ZONE_TYPES = \
    ["dic", "tra", "con", "int", "bio", "tex", "sol", "pic", "sli", "ani",
     "vid", "aud", "tab", "dia", "mod", "map", "rul"]

DEFAULT_ZONE_TYPES = ["dic", "tra", "con"]

# autozones that must be placed near the start of the page in the order given
START_AUTOZONES = ["dic"]

# autozones that must be placed at the end of the page in the order given
END_AUTOZONES = ["tra", "con"]

# zones that shoukd appear on every page in paragraph
PASS_THROUGH_ZONES = ["dic"]

MARGINS = ["l", "r", "lr"]

ZONE_ICONS = dict((zone_type, QtGui.QImage("buttons/Icons/icon_%s.png" % zone_type))
                  for zone_type in ZONE_TYPES)
