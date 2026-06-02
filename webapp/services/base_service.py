_MAX_USER_QUESTION_CHARS = 3000


class BaseService:
    def __init__(self):
        pass

    def _normalize_user_input(self, _input):
        if isinstance(_input, list):
            return [self._normalize_user_input(item) for item in _input]
        if _input is None:
            return ""
        return str(_input).strip()[:_MAX_USER_QUESTION_CHARS]
