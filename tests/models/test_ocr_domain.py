from webapp.models.ocr_domain import Ocr


def test_ocr_model_has_created_at_default():
    field = Ocr._fields["created_at"]

    assert field.default is not None
