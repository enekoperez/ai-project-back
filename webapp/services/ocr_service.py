import json

from webapp.dto.ocr_dto import ocr_to_dict
from webapp.prompts.ocr_prompt import build_system_prompt, build_user_prompt
from webapp.repositories.ocr_log_repository import OcrLogRepository
from webapp.services.ai_service import AiService
from webapp.services.base_service import BaseService


class OcrService(BaseService):
    def __init__(self):
        super().__init__()
        self.ai_service = AiService()
        self.ocr_log_repository = OcrLogRepository()

    @staticmethod
    def _try_json_loads(s):
        try:
            return json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return s

    def ask(self, request_json):
        ocr_log = self.ocr_log_repository.create()

        file_url = request_json["file_url"]
        questions = self._normalize_user_input(_input=request_json["questions"])

        chat_api_response, *_ = self.ai_service.call_llm(
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(questions=questions),
            response_format=self._response_format(questions=questions),
            document_data={"url": file_url, "extension": "pdf"},
        )
        response = self._try_json_loads(s=chat_api_response)
        return ocr_to_dict(db_obj=ocr_log, response=response)

    @staticmethod
    def _response_format(questions):
        properties = {
            question: {
                "type": "array",
                "items": {"type": "string"},
                "description": f"All values found for {question}",
            }
            for question in questions
        }

        response_format = {
            "type": "object",
            "properties": properties,
            "required": questions,
        }
        return response_format
