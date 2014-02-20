#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from tocelem import QTocElem


class QObjectElem(QtGui.QStandardItem):
    def __init__(self, oid, block_id, rubric, name=None):
        super(QObjectElem, self).__init__()
        self.oid = oid
        self.block_id = block_id
        oid_parts = self.oid.split('-', 4)
        self.type = oid_parts[-1]
        self.zone_num = oid_parts[2]
        self.page = int(oid_parts[1])
        self.name = name
        self.rubric = rubric
        self.setText(oid)
        self.setEditable(False)
        self.setSelectable(False)

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

    @property
    def display_name(self):
        return self.block_id

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
        self.rubric = objects[0].rubric if len(objects) > 0 else ""
        self.number = objects[0].zone_num if len(objects) > 0 else ""
        # a list of child objects
        self.objects = objects
        self.setText(type + name)
        self.setEditable(False)
        for obj in self.objects:
            self.appendRow(obj)

    @property
    def cas_id(self):
        return self.parent.cas_id

    # last 3 symbols of objects' oid
    @property
    def pdf_rubric(self):
        if len(self.objects) > 0:
            return self.objects[0].type
        return ""

    @property
    def zone_id(self):
        if len(self.objects) == 0:
            return ""
        else:
            return self.objects[0].zone_id

    @property
    def is_autoplaced(self):
        if len(self.objects) > 0:
            return self.objects[0].is_autoplaced
        return False

    def objects_as_dictslist(self):
        return [{"oid": o.oid,
                 "block-id": o.block_id } for o in self.objects]

    @property
    def page(self):
        if len(self.objects) == 0:
            return 0
        else:
            return self.objects[0].page


class QMarkerTocElem(QTocElem):
    # TODO perhaps make dependant on pic's height
    AUTOZONE_HEIGHT = 30

    # objects = {oid, block-id, rubric}
    def __init__(self, name, cas_id, objects):
        super(QMarkerTocElem, self).__init__(name, cas_id)
        self.setText(name)
        self.setEditable(False)
        # will be changed later as start\end marks appear
        self.auto_groups = {}
        # objects NOT automatically grouped
        self.groups = {}
        self.zones = []
        # now group automatically placed objects. Types can be Dic, Tra, Con
        for obj in objects:
            child = QObjectElem(obj["oid"], obj["block-id"], obj["rubric"])
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
            zone = QZone(self, zone, self.groups[zone])
            self.appendRow(zone)
            self.zones.append(zone)
        self._process_zone(QZone.AUTO_TRA)
        self._process_zone(QZone.AUTO_CON)
        # no modifications unless filled-in!
        self._set_selectable(False)

    @property
    def autozones(self):
        return [z for z in self.zones if z.is_autoplaced]

    def _process_zone(self, zone):
        if zone in self.auto_groups.keys():
            new_zone = QZone(self, zone, self.auto_groups[zone])
            self.appendRow(new_zone)
            self.zones.append(new_zone)

    def get_autozones_as_dict(self):
        result = []
        for auto in self.autozones:
            key_type = auto.zone_id
            zone = { "type": key_type,
                     "rel-start": self.get_start(key_type),
                     "rel-end": self.get_end(key_type),
                     "type": auto.type,
                     "rubric": auto.pdf_rubric,
                     "zone-id": auto.zone_id,
                     "number": auto.number,
                     "page": auto.page,
                     "objects": auto.objects_as_dictslist()
                    }
            result.append(zone)
        return result

    # return QZone elem with corr. zone_id
    def get_zone(self, zone_id):
        return next((z for z in self.zones if z.zone_id == zone_id), None)

    def set_finished(self, value):
        if value:
            self.state = self.STATE_FINISHED
        else:
            self.state = self.STATE_NOT_STARTED
        self._set_selectable(value)

    def _set_selectable(self, value):
        self.setSelectable(value)
        for zone in self.zones:
            zone.setSelectable(value)

    def get_start(self, zone):
        if zone == QZone.AUTO_DIC:
            return 0
        return None

    def get_end(self, zone):
        if zone == QZone.AUTO_CON:
            return -self.AUTOZONE_HEIGHT
        elif zone == QZone.AUTO_CON:
            mult = 2 if QZone.AUTO_TRA in self.auto_groups.keys() else 1
            return -self.AUTOZONE_HEIGHT * mult
        elif zone == QZone.AUTO_TRA:
            mult = 3 if QZone.AUTO_TRA in self.auto_groups.keys() else 2
            return -self.AUTOZONE_HEIGHT * mult
        return None
