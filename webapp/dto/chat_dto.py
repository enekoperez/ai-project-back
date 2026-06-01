def chat_to_dict(db_obj, response):
    return {
        "id": str(db_obj.id),
        "created_at": db_obj.created_at.isoformat() if db_obj.created_at else None,
        "response": response,
    }
