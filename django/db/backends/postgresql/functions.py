from django.db.models import Func


class JSONBBuildArray(Func):
    function = "JSONB_BUILD_ARRAY"
