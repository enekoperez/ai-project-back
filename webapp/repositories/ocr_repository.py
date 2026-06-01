from webapp.models.ocr_domain import Ocr


class OcrRepository:
    def create(self):
        return Ocr.objects.create()

    def get_all(self):
        return Ocr.objects.order_by("-created_at")
