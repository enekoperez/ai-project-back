from webapp.models.ocr_log_domain import OcrLog


class OcrLogRepository:
    @staticmethod
    def create():
        return OcrLog.objects.create()
