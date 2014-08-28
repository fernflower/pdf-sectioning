import json
from cmsquerymodule import CmsQueryModule


class OfflineCmsQueryModule(CmsQueryModule):
    DEFAULT_CONFIG = "offline-data/offline_config"
    OFFLINE_COURSE = "offline-data/offline_course"

    def _fetch_data(self, filename, login=None, password=None):
        data = None
        try:
            with open(filename) as f:
                data = f.readlines()
        except:
            # Yep, that sucks, but that's only for Demo - the tool has NEVER
            # BEEN planned and WILL NEVER be used offline
            pass
        return (200, data)

    def search_for_course(self, name_part, login=None, password=None):
        return [("Just a demo course", self.OFFLINE_COURSE)]

    def get_cms_course_toc(self, login, password, course_id=None,
                           progress=None):
        toc = [json.loads(t) for t in self._fetch_data(self.OFFLINE_COURSE)[1]]
        autotypes = self._get_autozone_types(toc)
        return (toc, autotypes)
