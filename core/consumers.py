import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage, Thread

User = get_user_model()


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('socket connected', event)
        user = self.scope['user']
        chat_room = f'user_chatroom_{user.id}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        # accept connection from client
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('receive', event)
        received_data = json.loads(event['text'])
        msg = received_data.get('message')
        sender_id = received_data.get('from')
        receiver_id = received_data.get('to')
        thread_id = received_data.get('thread_id')

        if not msg:
            print('Error:: EMPTY MESSAGE')
            return False
        sender = await self.get_user(sender_id)
        receiver = await self.get_user(receiver_id)
        thread_obj = await self.get_thread(thread_id)

        if not sender:
            print("ERROR:: SENDER not found")
        if not receiver:
            print("ERROR:: RECEIVER not found")
        if not thread_obj:
            print('Error:: Thread id is incorrect')
        msg_obj = await self.create_message(thread_obj, sender, msg)
        sendto_user_chatroom = f'user_chatroom_{receiver_id}'
        print(f'SEND TO {sendto_user_chatroom} and {self.chat_room}')
        self_user = self.scope['user']
        response = {
            'message': {
                'content': msg,
                'timestamp': msg_obj.get_timestamp(),
            },
            'sent_from': {
                'id': self_user.id,
                'username': self_user.username,
                'profile_pic': '#'
            },
            'thread_id': thread_id,
        }
        # send two copies of message to both users
        await self.channel_layer.group_send(
            sendto_user_chatroom,
            {
                # trigger event
                'type': 'chat_message',
                'text': json.dumps(response, default=str)
            }
        )
        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response, default=str)
            }
        )

        # await self.send({
        #     "type": "websocket.send",
        #     "text": json.dumps(response)
        # })

    async def websocket_disconnect(self, event):
        print('disconnect', event)

    async def chat_message(self, event):
        print('chat_message', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    @database_sync_to_async
    def get_user(self, user_id):
        qs = User.objects.filter(id=user_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=thread_id)
        if qs.exists():
            obj = qs.first()
            obj.save(update_fields=['updated_at'])
        else:
            obj = None
        return obj

    @database_sync_to_async
    def create_message(self, thread, user, msg):
        try:
            msg_obj = ChatMessage.objects.create(
                thread=thread, user=user, message=msg)
        except Exception as e:
            msg_obj = None
            print('Error:: Message not created', e)
        return msg_obj
