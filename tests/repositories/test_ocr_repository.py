from unittest.mock import Mock

from webapp.repositories.ocr_repository import OcrRepository


def test_ocr_repository_create_delegates_to_model(monkeypatch):
    ocr_model = Mock()
    ocr_model.objects.create.return_value = "created-ocr"
    monkeypatch.setattr("webapp.repositories.ocr_repository.Ocr", ocr_model)

    assert OcrRepository().create() == "created-ocr"
    ocr_model.objects.create.assert_called_once_with()
