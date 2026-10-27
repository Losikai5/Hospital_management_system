import json
import logging

from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

from ai.orchestrator import ask_assistant

logger = logging.getLogger(__name__)


class AIChatConsumer(WebsocketConsumer):
    def send_message(self, message_type, message):
        self.send(text_data=json.dumps({"type": message_type, "message": message}))

    def connect(self):
        # Anonymous visitors are allowed general-knowledge conversations.
        self.accept()
        self.send_message("connection", "Connected to AI assistant.")

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None or bytes_data is not None:
            self.send_message("error", "Send a JSON text message.")
            return
        if len(text_data.encode("utf-8")) > settings.AI_CHAT_MAX_MESSAGE_BYTES:
            self.send_message("error", "Message is too large.")
            return
        try:
            data = json.loads(text_data)
        except (ValueError, RecursionError):
            self.send_message("error", "Invalid JSON message.")
            return
        question = data.get("message") if isinstance(data, dict) else None
        if not isinstance(question, str) or not question.strip():
            self.send_message("error", "A non-empty text message is required.")
            return
        try:
            # Only trusted middleware scope supplies identity, never the payload.
            result = ask_assistant(question.strip(), user=self.scope.get("user"))
            answer = result["answer"]
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Invalid assistant response")
        except Exception:
            # Provider/DB exceptions may contain prompts or credentials. Do not
            # log the exception, payload, user, or generated content.
            logger.warning("AI request failed.")
            self.send_message("error", "The assistant is temporarily unavailable. Please try again.")
            return
        self.send_message("answer", answer)

    def disconnect(self, close_code):
        pass
