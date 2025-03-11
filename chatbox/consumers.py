import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .robot import set_mode, send_lesson_content
from asgiref.sync import sync_to_async


class ClassConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "classroom"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        if message == "start_lesson":
            await sync_to_async(set_mode)("lecturer")
            await send_lesson_content(self.room_group_name)

    async def classroom_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}))
