def ocr_to_dict(ocr):
    return {
        "id": str(ocr.id),
        "created_at": ocr.created_at.isoformat() if ocr.created_at else None,
    }
