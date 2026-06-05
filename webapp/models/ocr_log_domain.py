from mongoengine import DateTimeField, Document

from webapp.datetime_utils import utc_now


class OcrLog(Document):
    created_at = DateTimeField(default=utc_now)
