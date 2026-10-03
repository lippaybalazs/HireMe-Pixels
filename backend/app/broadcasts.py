from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

BOARD_GROUP = "board"


def broadcast_pixels(pixels):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        BOARD_GROUP,
        {
            "type": "board.update",
            "pixels": [
                {
                    "x": pixel.x,
                    "y": pixel.y,
                    "color": pixel.color,
                    "user": pixel.user,
                }
                for pixel in pixels
            ],
        },
    )
