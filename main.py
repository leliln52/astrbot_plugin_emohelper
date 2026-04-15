from snownlp import SnowNLP
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
class MyPlugin(Star):
    max_history_length = 20
    def __init__(self, context: Context):
        super().__init__(context)
        self.contexts = {}
    def get_context(self, session_id: str) -> list:
        if session_id not in self.contexts:
            self.contexts[session_id] = []
        return self.contexts[session_id]
    def add_to_context(self, session_id: str, message: str,event: AstrMessageEvent):
        context = self.get_context(session_id)
        user_id = event.sender.user_id
        context.append({
            "role": "user", 
            "user_id": user_id, 
            "content": message
        })
        if len(context) > self.max_history_length:
            context.pop(0)
    def prompt_joint(self, context):
        a=0
        prompt = ""
        while a < len(context):
            prompt += str(context[a])
            a += 1
        return prompt
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        message_str = event.message_str
        if not message_str or not message_str.strip():
            return
        s = SnowNLP(message_str)
        umo = event.unified_msg_origin
        provider_id = await self.context.get_current_chat_provider_id(umo=umo)
        score = s.sentiments
        logger.info(f"{message_str}的情感分析值为{score}")
        if message_str == "test":
            yield event.plain_result(f"{message_str}的情感分析值为{score}")
        if score <= 0.4:
            session_id = event.session_id
            context = self.get_context(session_id)
            history_prompt = self.prompt_joint(context)
            llm_resp = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt="用户之间疑似遇到了争吵或者心情不好，请你根据上下文进行回复\n\n" + history_prompt
            )
            ai_reply = llm_resp.completion_text
            yield event.plain_result(ai_reply)
