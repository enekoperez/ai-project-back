from webapp.prompts.chat_weather_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.tools.chat_weather_tools import ChatWeatherTools


class ChatWeatherService(BaseService):
    def chat(self, user_id, request_json):
        question = self._normalize_user_input(_input=request_json["question"])

        chat_log_key, _ = self._create_chat_log_key_and_display_name(user_id=user_id, key_2="chat_weather")
        chat_weather_tools = ChatWeatherTools()

        chat_log, chat_api_response = self._call_llm_and_log(
            user_question=question,
            chat_log_key=chat_log_key,
            system_prompt=build_system_prompt(),
            user_prompt=build_user_prompt(question=question),
            is_chat=True,
            tool_declarations=chat_weather_tools.declarations(),
            tool_dispatch=chat_weather_tools.dispatch(),
        )
        return self._chat_output(chat_log=chat_log, chat_api_response=chat_api_response)
