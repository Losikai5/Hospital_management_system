import json

from channels.generic.websocket import WebsocketConsumer

from ai.orchestrator import ask_assistant


class AIChatConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()

        self.send(text_data=json.dumps({
            "type": "connection",
            "message": "Connected to AI assistant.",
        }))

    def receive(self, text_data):
        data = json.loads(text_data)

        question = data.get("message")

        if not question:
            self.send(text_data=json.dumps({
                "type": "error",
                "message": "Message is required.",
            }))
            return

        user = self.scope["user"]

        result = ask_assistant(
            question,
            user=user,
        )

        self.send(text_data=json.dumps({
            "type": "answer",
            "message": result["answer"],
        }))

    def disconnect(self, close_code):
        pass
