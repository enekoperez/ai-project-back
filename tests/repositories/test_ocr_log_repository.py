from unittest.mock import Mock

from webapp.repositories.ocr_log_repository import OcrLogRepository


def test_ocr_log_repository_create_delegates_to_model(monkeypatch):
    ocr_log_model = Mock()
    ocr_log_model.objects.create.return_value = "created-ocr"
    monkeypatch.setattr("webapp.repositories.ocr_log_repository.OcrLog", ocr_log_model)

    assert OcrLogRepository().create() == "created-ocr"
    ocr_log_model.objects.create.assert_called_once_with()
