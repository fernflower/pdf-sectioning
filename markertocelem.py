#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from tocelem import QTocElem


class QObjectElem(QtGui.QStandardItem):
    def __init__(self, oid, block_id, name=None):
        super(QObjectElem, self).__init__()
        self.oid = oid
        self.block_id = block_id
        oid_parts = self.oid.split('-', 4)
        self.type = oid_parts[-1]
        self.zone_num = oid_parts[2]
        self.page = int(oid_parts[1])
        self.name = name
        self.setText(oid)
        self.setEditable(False)

    # if oid's third position consists of 00, then this object can be placed
    # automatically
    @property
    def is_autoplaced(self):
        return self.zone_num == '00'

    @property
    def zone_id(self):
        if self.is_autoplaced:
            return self.type
        else:
            return self.zone_num + self.type

# creates an item with objects as it's children
class QZone(QtGui.QStandardItem):
    AUTO_DIC = "dic"
    AUTO_TRA = "tra"
    AUTO_CON = "con"

    def __init__(self, parent, type, objects, name=""):
        super(QZone, self).__init__()
        self.parent = parent
        self.type = type
        self.name = name
        # a list of child objects
        self.objects = objects
        self.setText(type + name)
        self.setEditable(False)
        for obj in self.objects:
            self.appendRow(obj)

    @property
    def cas_id(self):
        return self.parent.cas_id

    @property
    def zone_id(self):
        if len(self.objects) == 0:
            return ""
        else:
            return self.objects[0].zone_id


class QMarkerTocElem(QtGui.QStandardItem):
    # TODO perhaps make dependant on pic's height
    AUTOZONE_HEIGHT = 20

    def __init__(self, name, cas_id, objects):
        super(QMarkerTocElem, self).__init__()
        self.name = name
        self.cas_id = cas_id
        self.setText(name)
        self.setEditable(False)
        self.auto_groups = {}
        # objects NOT automatically grouped
        self.groups = {}
        # now group automatically placed objects. Types can be Dic, Tra, Con
        for obj in objects:
            child = QObjectElem(obj["oid"], obj["block-id"])
            # 00type marks autogroup, type - groups objects by type which can't
            # be placed automatically
            def _add_obj(groups):
                try:
                    groups[child.zone_id].append(child)
                except KeyError:
                    groups[child.zone_id] = [child]

            if child.is_autoplaced:
                _add_obj(self.auto_groups)
            else:
                _add_obj(self.groups)

        # now add all elems in correct order: DIC, ...  any other... , TRA, CON
        self._process_zone(QZone.AUTO_DIC)
        for zone in self.groups.keys():
            self.appendRow(QZone(self, zone, self.groups[zone]))
        self._process_zone(QZone.AUTO_TRA)
        self._process_zone(QZone.AUTO_CON)

    def _process_zone(self, zone):
        if zone in self.auto_groups.keys():
            self.appendRow(QZone(self, zone, self.auto_groups[zone]))

    def get_autozones_as_dict(self):
        result = []
        for auto, objects in self.auto_groups.items():
            zone = { "type": auto,
                     "rel-start": self.get_start(auto),
                     "rel-end": self.get_end(auto),
                     "objects": objects
                    }
            result.append(zone)
        return result

    def get_start(self, zone):
        if zone == QZone.AUTO_DIC:
            return 0
        else: None

    def get_end(self, zone):
        if zone == QZone.AUTO_CON:
            return - self.AUTOZONE_HEIGHT
        elif zone == QZone.AUTO_CON:
            mult = 2 if QZone.AUTO_TRA in self.auto_groups.keys() else 1
            return -self.AUTOZONE_HEIGHT * mult
