#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui


ZONE_TYPES = \
    ["dic", "tra", "con", "int", "bio", "tex", "sol", "pic", "sli", "ani",
     "vid", "aud", "tab", "dia", "mod", "map", "rul"]


ZONE_ICONS = dict((zone_type, QtGui.QImage("buttons/Icons/icon_%s.png" % zone_type))
                  for zone_type in ZONE_TYPES)
