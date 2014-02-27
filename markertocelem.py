#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from tocelem import QStatefulElem, QTocElem
from stylesheets import GENERAL_STYLESHEET, LIST_ITEM_DESELECT
from zonetypes import START_AUTOZONES, END_AUTOZONES, ZONE_ICONS


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
        self.setEditable(False)
        self.setSelectable(False)
        self.setText(self.display_name)

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
        return "%s\n(%s)" % (self.name, self.oid) \
            if self.name is not None else self.oid

# creates an item with objects as it's children
class QZone(QStatefulElem):
    def __init__(self, parent, type, objects, name=""):
        super(QZone, self).__init__(type)
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


    def is_on_page(self, page):
        return self.page == page

class QMarkerTocElem(QTocElem):
    def __init__(self, name, cas_id, objects):
        super(QMarkerTocElem, self).__init__(name, cas_id)
        self.setText(name)
        self.setEditable(False)
        # will be changed later as start\end marks appear
        self.auto_groups = {}
        # objects NOT automatically grouped
        self.groups = {}
        self.zones = []
        # objects = {oid, block-id, rubric}
        # now group automatically placed objects. Types can be Dic, Tra, Con
        for obj in objects:
            child = QObjectElem(obj["oid"], obj["block-id"],
                                obj["rubric"], obj["name"])
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
        for zone in START_AUTOZONES:
            self._process_zone(zone)
        for zone in self.groups.keys():
            zone = QZone(self, zone, self.groups[zone])
            self.appendRow(zone)
            self.zones.append(zone)
        for zone in END_AUTOZONES:
            self._process_zone(zone)
        # no modifications unless filled-in!
        self._set_selectable(False)

    @property
    def autozones(self):
        return [z for z in self.zones if z.is_autoplaced]

    @property
    def all_zones_placed(self):
        return all(map(lambda z: z.is_finished(), self.zones))

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
        self.update()

    def _set_selectable(self, value):
        self.setSelectable(value)
        for zone in self.zones:
            zone.setSelectable(value)

    def select_on_page(self, page):
        map(lambda z: z.deselect(),
            [z for z in self.zones if z.page != page])
        map(lambda z: z.select(),
            [z for z in self.zones if z.page == page])

    def get_start(self, zone):
        if zone not in START_AUTOZONES:
            return None
        return [z for z in self.auto_groups.keys()
                if z in START_AUTOZONES].index(zone) * ZONE_ICONS[zone].height()

    def get_end(self, zone):
        if zone not in END_AUTOZONES:
            return None
        end_present = [z for z in self.auto_groups.keys() if z in END_AUTOZONES]
        mult = len(end_present) - end_present.index(zone)
        return -ZONE_ICONS[zone].height() * mult
