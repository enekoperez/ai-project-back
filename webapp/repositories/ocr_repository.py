from webapp.models.ocr_domain import Ocr


class OcrRepository:
    @staticmethod
    def create():
        return Ocr.objects.create()
