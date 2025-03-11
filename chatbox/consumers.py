import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from nbformat import read
from .robot import play_audio_async, set_mode, RobotStatus
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
            await self.send_lesson_content()

    # TODO: send lesson content should be snapshot..
    # Full contents should be in Robot.
    async def send_lesson_content(self):
        try:
            notebook_path = (
                "chatbox/static/chatbox/mm-course/lang/eng/family/01_family.ipynb"
            )

            print(notebook_path)
            with open(notebook_path) as f:
                notebook = read(f, as_version=4)
        except FileNotFoundError:
            print("Lesson file not found.")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "classroom_message", "message": {"type": "sof"}},
        )

        for idx, cell in enumerate(notebook.cells):
            if cell.cell_type == "code":
                source = cell.source
                if "Image(" in source:
                    image_path = source.split('"')[1]
                    full_image_path = "chatbox/mm-course/lang/eng/family/" + image_path
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "classroom_message",
                            "message": {"type": "image", "path": full_image_path},
                        },
                    )
                elif "Audio(" in source:
                    audio_path = source.split('"')[1]
                    full_audio_path = (
                        "chatbox/static/chatbox/mm-course/lang/eng/family/" + audio_path
                    )
                    # Save current lesson state before playing audio
                    await sync_to_async(self._save_lesson_state)(notebook_path, idx)
                    await play_audio_async(full_audio_path)
                elif "print(" in source:
                    print_text = source.split('print("')[1].split('")')[0]
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "classroom_message",
                            "message": {"type": "text", "content": print_text},
                        },
                    )
                elif "clear_output(wait=True)" in source:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {"type": "classroom_message", "message": {"type": "clear"}},
                    )
                    await asyncio.sleep(2)

        # Send EOF message after processing all cells
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "classroom_message", "message": {"type": "eof"}},
        )

    def _save_lesson_state(self, notebook_path, current_cell_index):
        """Save the current lesson state to RobotStatus memory"""
        robot_status = RobotStatus.objects.get(pk=1)
        robot_status.memory["current_lesson"] = {
            "notebook_path": notebook_path,
            "cell_index": current_cell_index,
        }
        robot_status.save()

    async def classroom_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}))
