from webapp.models.ocr_domain import Ocr


class OcrRepository:
    def create(self):
        return Ocr.objects.create()
