from webapp.dto.ocr_dto import ocr_to_dict
from webapp.repositories.ocr_repository import OcrRepository


class OcrService:
    def __init__(self):
        self.ocr_repository = OcrRepository()

    def create(self):
        return ocr_to_dict(self.ocr_repository.create())

    def get_all(self):
        return [ocr_to_dict(ocr) for ocr in self.ocr_repository.get_all()]
