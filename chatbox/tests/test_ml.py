from django.test import TestCase
from unittest import skipIf
from openai import AsyncOpenAI
from django.conf import settings
import groq


@skipIf(not settings.OPENAI_API_KEY, reason="Needs openai api key")
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


@skipIf(not settings.GROQ_API_KEY, reason="Needs groq api key")
class GroqTestCase(TestCase):
    def setUp(self):
        self.client = groq.Client(api_key=settings.GROQ_API_KEY)

    def test_transcribe_audio(self):
        filename = "chatbox/res/react_sara.wav"

        with open(filename, "rb") as f:
            try:
                completion = self.client.audio.transcriptions.create(
                    model="distil-whisper-large-v3-en",
                    file=(filename, f.read()),
                    response_format="text",
                )
                print(completion.text)
            except Exception as e:
                return f"Error in transcription: {str(e)}"

    def test_generate_response(self):

        try:
            # Use Llama 3 70B powered by Groq for text generation
            completion = self.client.chat.completions.create(
                model="llama-3.2-1b-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful english teacher."},
                    {"role": "user", "content": "What is cat?"},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error in response generation: {str(e)}"
