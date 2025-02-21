from django.test import TestCase
from openai import AsyncOpenAI


class OpenAITestCase(TestCase):
    def setUp(self):
        self.client = AsyncOpenAI()

    def test_conversation(self):
        with self.client.beta.realtime.connect(
            model="gpt-4o-realtime-preview"
        ) as connection:
            connection.session.update(session={"modalities": ["text"]})

            connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Say hello!"}],
                }
            )
            connection.response.create()

            for event in connection:
                if event.type == "response.text.delta":
                    print(event.delta, flush=True, end="")

                elif event.type == "response.text.done":
                    print()

                elif event.type == "response.done":
                    break
