def chat_to_dict(chat):
    return {
        "id": str(chat.id),
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
    }
