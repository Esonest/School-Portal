# liveclass/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LiveClassConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.live_class_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f'liveclass_{self.live_class_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'sender': data.get('sender'),
                'action': data.get('action')  # e.g., "raise_hand"
            }
        )

    # Receive message from group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
