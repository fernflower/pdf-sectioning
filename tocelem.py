#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from stylesheets import GENERAL_STYLESHEET, LIST_ITEM_DESELECT
from zonetypes import ZONE_ICONS


class QStatefulElem(QtGui.QStandardItem):
    STATE_NOT_STARTED = "not_started"
    STATE_FINISHED = "finished"

    # unfortunately could not find a way of setting this up from stylesheet
    ICONS = {STATE_NOT_STARTED: "buttons/Not_done.png",
             STATE_FINISHED: "buttons/All_done.png"}

    def __init__(self, name):
        super(QStatefulElem, self).__init__(name)
        self.name = name
        self.state = self.STATE_NOT_STARTED
        self.setEditable(False)

    def set_finished(self, value):
        if value:
            self.state = QTocElem.STATE_FINISHED
        else:
            self.state = QTocElem.STATE_NOT_STARTED
        self.update()

    def set_not_started(self):
        self.state = QTocElem.STATE_NOT_STARTED
        self.update()

    def update(self):
        # set widget design according to it's state
        self.setIcon(QtGui.QIcon(self.ICONS[self.state]))

    def is_finished(self):
        return self.state == QTocElem.STATE_FINISHED

    def is_not_started(self):
        return self.state == QTocElem.STATE_NOT_STARTED


class QTocElem(QStatefulElem):
    STATE_WRONG_START_END = "wrong_start_end"
    STATE_NOT_FINISHED = "not_finished"
    STATE_BRACKETS_ERROR = "brackets_error"

    # unfortunately could not find a way of setting this up from stylesheet
    ICONS = {QStatefulElem.STATE_NOT_STARTED: "buttons/Not_done.png",
             STATE_NOT_FINISHED: "buttons/Half_done.png",
             STATE_WRONG_START_END: "buttons/Half_done.png",
             STATE_BRACKETS_ERROR: "buttons/Half_done.png",
             QStatefulElem.STATE_FINISHED: "buttons/All_done.png"}

    # here come error messages
    ERROR_MESSAGES = \
        { STATE_NOT_FINISHED: u"Ошибка в разметке: Не хватает одной из меток",
          STATE_WRONG_START_END: \
             u"Ошибка в разметке: конец параграфа стоит выше начала",
          STATE_BRACKETS_ERROR: \
             u"Ошибка в разметке: начало параграфа между началом и концом другого"}

    def __init__(self, name, cas_id):
        super(QTocElem, self).__init__(name)
        self.cas_id = cas_id
        self.state = self.STATE_NOT_STARTED
        self.setEditable(False)

    def update(self):
        # set widget design according to it's state
        self.setIcon(QtGui.QIcon(self.ICONS[self.state]))

    def set_finished(self, value):
        if value:
            self.state = QTocElem.STATE_FINISHED
        else:
            self.state = QTocElem.STATE_NOT_FINISHED
        self.update()

    def set_brackets_error(self):
        self.state = self.STATE_BRACKETS_ERROR
        self.update()

    def set_mixed_up_marks(self):
        self.state = self.STATE_WRONG_START_END
        self.update()

    def get_message(self):
        return self.ERROR_MESSAGES[self.state]

    def is_error(self):
        return self.state in \
            [self.STATE_NOT_FINISHED, self.STATE_WRONG_START_END,
             self.STATE_BRACKETS_ERROR]


class QObjectElem(QtGui.QStandardItem):
    def __init__(self, oid, block_id, rubric, name=None):
        super(QObjectElem, self).__init__()
        self.oid = oid
        self.block_id = block_id
        oid_parts = self.oid.split('-', 4)
        # there can be two types of oids: normal ones, consisting of 5
        # sections: book-page-zonenum-objnum-type
        # and inner object's ids, consisting of 4 sections:
        # book-page-zonenum-type
        # INNER ZONE MUST HAVE DIFFERENT SECTION ID (ex. inner_section)
        self.type = oid_parts[-1]
        self.zone_num = oid_parts[2] if len(oid_parts) > 3 else ""
        self.page = int(oid_parts[1]) if len(oid_parts) > 3 else 0
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
    def is_inner(self):
        return "inner" in self.type

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
    def __init__(self, parent, type, objects):
        super(QZone, self).__init__(type)
        self.parent = parent
        self.number = objects[0].zone_num if len(objects) > 0 else ""
        # a list of child objects
        self.objects = objects
        self.setEditable(False)
        for obj in self.objects:
            self.appendRow(obj)
        self.setText(self.zone_id)

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

    @property
    def is_inner(self):
        if len(self.objects) > 0:
            return self.objects[0].is_inner
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

    def set_finished(self, value):
        super(QZone, self).set_finished(value)
        # notify parent that state has changed
        self.parent.notify_state_changed(self)


class QAutoZoneContainer(QStatefulElem):
    def __init__(self, parent):
        super(QAutoZoneContainer, self).__init__(u"авто")
        self.setSelectable(True)
        # a list of autozones
        self.zones = []
        self.parent = parent

    def add_zone(self, zone_type, objects):
        zone = QZone(self.parent, zone_type, objects)
        self.appendRow(zone)
        self.zones.append(zone)
        return zone

    @property
    def cas_id(self):
        return self.parent.cas_id

    @property
    def all_zones_placed(self):
        return all(map(lambda z: z.is_finished(), self.zones))


class QMarkerTocElem(QTocElem):
    def __init__(self, name, cas_id, objects, start_autozones, end_autozones):
        super(QMarkerTocElem, self).__init__(name, cas_id)
        self.setText(name)
        self.setEditable(False)
        self.auto = None
        self.zones = []
        self.start_autozones = start_autozones
        self.end_autozones = end_autozones

        auto_data = {}
        non_auto_data = {}
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
                _add_obj(auto_data)
            else:
                _add_obj(non_auto_data)

        # now add all elems in correct order: DIC, ...  any other... , TRA, CON
        def _process_auto_zone(zone):
            if zone in auto_data.keys():
                if not self.auto:
                    self.auto = QAutoZoneContainer(self)
                    self.appendRow(self.auto)
                new_zone = self.auto.add_zone(zone, auto_data[zone])
                self.zones.append(new_zone)

        for zone in self.start_autozones:
            _process_auto_zone(zone)
        for zone in non_auto_data.keys():
            zone = QZone(self, zone, non_auto_data[zone])
            self.appendRow(zone)
            self.zones.append(zone)
        for zone in self.end_autozones:
            _process_auto_zone(zone)
        # if any other auto zones left (not belonging to start\end, place them
        # here)
        diff = set(auto_data.keys()) - \
            set(self.start_autozones).union(self.end_autozones)
        if diff != set([]):
            print "No start\end binding for %s" % diff
            for zone in diff:
                _process_auto_zone(zone)
        # no modifications unless filled-in!
        self._set_selectable(False)

    @property
    def autozones(self):
        return self.auto.zones if self.auto else []

    @property
    def autotypes(self):
        return set([z.zone_id for z in self.autozones])

    @property
    def all_zones_placed(self):
        return all(map(lambda z: z.is_finished(), self.zones))

    def set_not_started(self):
        super(QMarkerTocElem, self).set_not_started()
        if self.auto:
            self.auto.set_not_started()
        for zone in self.zones:
            zone.set_not_started()

    # only autozones that appear in start\end will be returned
    def get_autozones_as_dict(self):
        result = []
        for auto in [az for az in self.autozones if az.pdf_rubric in \
                     self.start_autozones + self.end_autozones]:
            key_type = auto.zone_id
            zone = { "rel-start": self._get_start(key_type),
                     "rel-end": self._get_end(key_type),
                     "rubric": auto.pdf_rubric,
                     "zone-id": auto.zone_id,
                     "page": auto.page,
                     "objects": auto.objects_as_dictslist()
                    }
            result.append(zone)
        return result

    # return QZone elem with corr. zone_id
    def get_zone(self, zone_id):
        return next((z for z in self.zones if z.zone_id == zone_id), None)

    def _set_selectable(self, value):
        self.setSelectable(value)
        for zone in self.zones:
            zone.setSelectable(value)

    def select_on_page(self, page):
        map(lambda z: z.deselect(),
            [z for z in self.zones if z.page != page])
        map(lambda z: z.select(),
            [z for z in self.zones if z.page == page])

    def notify_state_changed(self, zone):
        if zone.is_autoplaced:
            self.auto.set_finished(self.auto.all_zones_placed)
        self.set_finished(self.all_zones_placed)
        self.update()

    def _get_start(self, zone):
        start_present = [z.zone_id for z in self.autozones
                         if z.zone_id in self.start_autozones]
        if zone not in start_present:
            return None
        return start_present.index(zone) * ZONE_ICONS[zone].height()

    def _get_end(self, zone):
        end_present = [z.zone_id for z in self.autozones
                       if z.zone_id in self.end_autozones]
        if zone not in end_present:
            return None
        mult = len(end_present) - end_present.index(zone)
        return -ZONE_ICONS[zone].height() * mult
