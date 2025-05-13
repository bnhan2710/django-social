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
        self.joined_threads = set()  # Track joined threads
        
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
        command = received_data.get('command')
        
        if command == 'join':
            await self.join_thread(received_data)
        elif command == 'new_message':
            await self.handle_new_message(received_data)
        else:
            print(f"ERROR:: Unknown command: {command}")
    
    async def join_thread(self, data):
        thread_id = data.get('thread_id')
        if not thread_id:
            print("ERROR:: Thread ID not provided")
            return
            
        # Add this channel to the thread's group
        thread_group = f'thread_{thread_id}'
        await self.channel_layer.group_add(
            thread_group,
            self.channel_name
        )
        
        # Track that we've joined this thread
        self.joined_threads.add(thread_id)
        
        print(f'Joined thread: {thread_id}')
    
    async def handle_new_message(self, data):
        msg = data.get('message')
        sender_id = data.get('from')
        thread_id = data.get('thread_id')

        if not msg:
            print('Error:: EMPTY MESSAGE')
            return False
            
        if not thread_id:
            print('Error:: Thread ID not provided')
            return False
            
        sender = await self.get_user(sender_id)
        thread_obj = await self.get_thread(thread_id)

        if not sender:
            print("ERROR:: SENDER not found")
            return
            
        if not thread_obj:
            print('Error:: Thread id is incorrect')
            return
            
        # Get the other user in the thread
        users = await self.get_thread_users(thread_obj)
        receiver = next((user for user in users if user.id != sender_id), None)
        
        if not receiver:
            print("ERROR:: Receiver not found in thread")
            return
            
        # Save the message to the database
        chat_msg = await self.create_chat_message(thread_obj, sender, msg)
        
        # Send message to thread group
        thread_group = f'thread_{thread_id}'
        await self.channel_layer.group_send(
            thread_group,
            {
                'type': 'chat_message',
                'message': msg,
                'user_id': sender_id,
                'thread_id': thread_id,
                'username': sender.username
            }
        )
        
        # Send notification to receiver's personal group
        receiver_room = f'user_chatroom_{receiver.id}'
        await self.channel_layer.group_send(
            receiver_room,
            {
                'type': 'chat_message',
                'message': msg,
                'user_id': sender_id,
                'thread_id': thread_id,
                'username': sender.username
            }
        )
    
    async def chat_message(self, event):
        """
        This method is called when something is sent to the group
        """
        # Send the message to the WebSocket
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps(event)
        })
    
    async def websocket_disconnect(self, event):
        print('socket disconnected', event)
        # Leave all joined thread groups
        for thread_id in self.joined_threads:
            thread_group = f'thread_{thread_id}'
            await self.channel_layer.group_discard(
                thread_group,
                self.channel_name
            )
        
        # Leave user's personal group
        await self.channel_layer.group_discard(
            self.chat_room,
            self.channel_name
        )
        
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
            
    @database_sync_to_async
    def get_thread(self, thread_id):
        try:
            return Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            return None
            
    @database_sync_to_async
    def get_thread_users(self, thread):
        # Get both users in the thread
        return [thread.first_person, thread.second_person]
        
    @database_sync_to_async
    def create_chat_message(self, thread, user, message):
        return ChatMessage.objects.create(thread=thread, user=user, message=message)
