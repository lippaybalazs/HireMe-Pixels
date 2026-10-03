import json

from channels.generic.websocket import AsyncWebsocketConsumer


BOARD_GROUP = "board"


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            BOARD_GROUP,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            BOARD_GROUP,
            self.channel_name,
        )

    async def board_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "board_update",
                    "pixels": event["pixels"],
                }
            )
        )