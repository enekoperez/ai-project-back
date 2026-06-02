from webapp.models.ocr_log_domain import OcrLog


def test_ocr_log_model_has_created_at_default():
    field = OcrLog._fields["created_at"]

    assert field.default is not None
