from django.test import TestCase
from openai import AsyncOpenAI
from django.conf import settings


class OpenAITestCase(TestCase):
    def setUp(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def test_conversation(self):
        async with self.client.beta.realtime.connect(
            model="gpt-4o-realtime-preview"
        ) as connection:
            await connection.session.update(session={"modalities": ["text"]})

            await connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Say hello!"}],
                }
            )
            await connection.response.create()

            async for event in connection:
                if event.type == "response.text.delta":
                    print(event.delta, flush=True, end="")

                elif event.type == "response.text.done":
                    print("done")

                elif event.type == "response.done":
                    break
                elif event.type == "error":
                    print(event.error.type)
                    print(event.error.code)
                    print(event.error.event_id)
                    print(event.error.message)
