import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage, Thread, Profile
from datetime import datetime
import traceback

User = get_user_model()


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        """
        Handle WebSocket connection
        """
        print('WebSocket connected', event)
        print(f"User authenticated: {self.scope['user'].is_authenticated}")
        print(f"User: {self.scope['user']}")
        
        # Initialize active_threads regardless of authentication
        self.active_threads = set()  # Track threads the user is actively viewing
        
        # Accept the WebSocket connection
        await self.send({
            'type': 'websocket.accept'
        })
        
        # Get the user from the scope
        user = self.scope['user']
        self.user = user
        
        # Check if the user is authenticated
        if not user.is_authenticated:
            print("ERROR: User not authenticated")
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'error',
                    'message': 'Authentication required',
                })
            })
            await self.send({
                'type': 'websocket.close',
                'code': 4003,
            })
            return
        
        # Set up user's personal notification room
        user_room = f'user_{user.id}'
        self.user_room = user_room
        
        try:
            # Add the user to their personal notification group
            await self.channel_layer.group_add(
                user_room,
                self.channel_name
            )
            print(f"User {user.username} (ID: {user.id}) added to notification group {user_room}")
            
            # Send initial status to client
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'connection_established',
                    'user_id': user.id,
                    'username': user.username
                })
            })
            
            # Get unread message counts
            try:
                unread_counts = await self.get_unread_counts(user)
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({
                        'type': 'unread_counts',
                        'counts': unread_counts
                    })
                })
            except Exception as unread_error:
                print(f"Error fetching unread counts: {str(unread_error)}")
                # Continue anyway - this is not critical
            
        except Exception as e:
            print(f"Error in websocket_connect: {str(e)}")
            print(traceback.format_exc())
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'error',
                    'message': f'Connection error: {str(e)}',
                })
            })

    async def websocket_receive(self, event):
        """
        Handle messages received from the client
        """
        try:
            data = json.loads(event['text'])
            command = data.get('command')
            
            if command == 'join_thread':
                await self.join_thread(data)
            elif command == 'leave_thread':
                await self.leave_thread(data)
            elif command == 'send_message':
                await self.send_message(data)
            elif command == 'mark_thread_read':
                await self.mark_thread_read(data)
            elif command == 'typing':
                await self.handle_typing(data)
            elif command == 'get_thread_messages':
                await self.get_thread_messages(data)
            else:
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({
                        'type': 'error',
                        'message': f'Unknown command: {command}'
                    })
                })
                
        except json.JSONDecodeError:
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                })
            })
        except Exception as e:
            error_msg = f"Error in websocket_receive: {str(e)}"
            print(error_msg)
            print(f"Command: {data.get('command', 'unknown')}")
            print(f"Data: {data}")
            traceback.print_exc()
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'error',
                    'message': f'Error: {str(e)}'
                })
            })

    async def join_thread(self, data):
        """
        Join a specific thread to receive messages
        """
        thread_id = data.get('thread_id')
        if not thread_id:
            return
        
        try:
            # Get the thread and verify the user is part of it
            thread = await self.get_thread(thread_id)
            if not thread:
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({
                        'type': 'error',
                        'message': 'Thread not found'
                    })
                })
                return
            
            # Check if user is part of this thread
            user_is_in_thread = await self.check_user_in_thread(thread, self.user)
            if not user_is_in_thread:
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({
                        'type': 'error',
                        'message': 'Not authorized for this thread'
                    })
                })
                return
            
            # Join the thread group
            thread_group = f'thread_{thread_id}'
            await self.channel_layer.group_add(
                thread_group,
                self.channel_name
            )
            
            # Add to active threads
            self.active_threads.add(thread_id)
            
            # Mark thread as read for this user
            await self.mark_thread_as_read(thread, self.user)
            
            # Get thread messages
            messages = await self.get_thread_message_data(thread)
            
            # Get other user profile using async-safe method
            other_user = await self.get_other_user(thread, self.user)
            other_user_profile = await self.get_user_profile(other_user)
        except Exception as e:
            print(f"Error in join_thread: {str(e)}")
            print(traceback.format_exc())
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({
                    'type': 'error',
                    'message': f'Thread error: {str(e)}'
                })
            })
            return
        
        # Send confirmation and thread data
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'thread_joined',
                'thread_id': thread_id,
                'messages': messages,
                'other_user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'profile_pic': other_user_profile.profile_pic.url if other_user_profile else None
                }
            })
        })
        
        print(f"User {self.user.username} joined thread {thread_id}")

    async def leave_thread(self, data):
        """
        Leave a specific thread
        """
        thread_id = data.get('thread_id')
        if not thread_id or thread_id not in self.active_threads:
            return
        
        thread_group = f'thread_{thread_id}'
        await self.channel_layer.group_discard(
            thread_group,
            self.channel_name
        )
        
        self.active_threads.remove(thread_id)
        
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'thread_left',
                'thread_id': thread_id
            })
        })
        
        print(f"User {self.user.username} left thread {thread_id}")

    async def send_message(self, data):
        """
        Send a new message in a thread
        """
        thread_id = data.get('thread_id')
        message_text = data.get('message')
        
        if not thread_id or not message_text or not message_text.strip():
            return
        
        thread = await self.get_thread(thread_id)
        if not thread:
            return
        
        # Check if user is part of this thread using the async method
        user_in_thread = await self.check_user_in_thread(thread, self.user)
        if not user_in_thread:
            return
        
        # Create the message
        message = await self.create_message(thread, self.user, message_text)
        
        # Update thread with last message
        await self.update_thread_last_message(thread, message_text)
        
        # Increment unread count for the other user
        await self.increment_thread_unread(thread, self.user)
        
        # Get user profile for the sender
        user_profile = await self.get_user_profile(self.user)
        
        # Get the other user using async method
        other_user = await self.get_other_user(thread, self.user)
        
        # Prepare message data - use proper timestamp formatting
        try:
            timestamp = message.timestamp.strftime("%b %d, %Y, %I:%M %p") if hasattr(message, 'timestamp') else "Unknown time"
        except Exception:
            timestamp = "Unknown time"
            
        message_data = {
            'id': message.id,
            'message': message.message,
            'user_id': self.user.id,
            'username': self.user.username,
            'timestamp': timestamp,
            'profile_pic': user_profile.profile_pic.url if user_profile else None
        }
        
        # Send to thread group
        await self.channel_layer.group_send(
            f'thread_{thread_id}',
            {
                'type': 'chat_message',
                'message_data': message_data,
                'thread_id': thread_id
            }
        )
        
        # Get unread count for the other user - this should be made async safe
        unread_count = await self.get_thread_unread_count(thread, other_user)
        
        await self.channel_layer.group_send(
            f'user_{other_user.id}',
            {
                'type': 'thread_notification',
                'thread_id': thread_id,
                'message': message_data,
                'unread_count': unread_count
            }
        )

    async def mark_thread_read(self, data):
        """
        Mark all messages in a thread as read
        """
        thread_id = data.get('thread_id')
        if not thread_id:
            return
        
        thread = await self.get_thread(thread_id)
        if not thread:
            return
        
        # Check if user is part of this thread using the async method
        user_in_thread = await self.check_user_in_thread(thread, self.user)
        if not user_in_thread:
            return
        
        # Mark thread as read
        await self.mark_thread_as_read(thread, self.user)
        
        # Send confirmation
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'thread_marked_read',
                'thread_id': thread_id
            })
        })

    async def handle_typing(self, data):
        """
        Handle typing indicator
        """
        thread_id = data.get('thread_id')
        is_typing = data.get('is_typing', False)
        
        if not thread_id:
            return
        
        thread = await self.get_thread(thread_id)
        if not thread:
            return
        
        # Check if user is part of this thread using the async method
        user_in_thread = await self.check_user_in_thread(thread, self.user)
        if not user_in_thread:
            return
        
        # Send typing indicator to thread group
        await self.channel_layer.group_send(
            f'thread_{thread_id}',
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'thread_id': thread_id,
                'is_typing': is_typing
            }
        )

    async def get_thread_messages(self, data):
        """
        Get messages for a thread
        """
        thread_id = data.get('thread_id')
        if not thread_id:
            return
        
        thread = await self.get_thread(thread_id)
        if not thread:
            return
        
        # Check if user is part of this thread using the async method
        user_in_thread = await self.check_user_in_thread(thread, self.user)
        if not user_in_thread:
            return
        
        # Get messages
        messages = await self.get_thread_message_data(thread)
        
        # Send messages to client
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'thread_messages',
                'thread_id': thread_id,
                'messages': messages
            })
        })

    async def chat_message(self, event):
        """
        Send chat message to client
        """
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'new_message',
                'thread_id': event['thread_id'],
                'message': event['message_data']
            })
        })

    async def thread_notification(self, event):
        """
        Send thread notification to client
        """
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'thread_notification',
                'thread_id': event['thread_id'],
                'message': event['message'],
                'unread_count': event['unread_count']
            })
        })

    async def typing_indicator(self, event):
        """
        Send typing indicator to client
        """
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps({
                'type': 'typing_indicator',
                'thread_id': event['thread_id'],
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            })
        })

    async def websocket_disconnect(self, event):
        """
        Handle WebSocket disconnection
        """
        print('WebSocket disconnected', event)
        
        # Leave all active threads
        if hasattr(self, 'active_threads') and self.active_threads:
            for thread_id in self.active_threads:
                try:
                    await self.channel_layer.group_discard(
                        f'thread_{thread_id}',
                        self.channel_name
                    )
                except Exception as e:
                    print(f"Error leaving thread {thread_id}: {str(e)}")
        
        # Leave user notification group
        if hasattr(self, 'user_room') and hasattr(self, 'channel_layer'):
            try:
                await self.channel_layer.group_discard(
                    self.user_room,
                    self.channel_name
                )
            except Exception as e:
                print(f"Error leaving user room {self.user_room}: {str(e)}")

    # Database access methods
    @database_sync_to_async
    def get_thread(self, thread_id):
        try:
            return Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, thread, user, message_text):
        msg = ChatMessage.objects.create(
            thread=thread,
            user=user,
            message=message_text
        )
        return msg

    @database_sync_to_async
    def mark_thread_as_read(self, thread, user):
        # Update the thread unread count field directly instead of calling thread.mark_as_read
        if thread.first_person == user:
            thread.first_person_unread = 0
        else:
            thread.second_person_unread = 0
        thread.save()
        
        # Also mark individual messages as read
        ChatMessage.objects.filter(
            thread=thread
        ).exclude(user=user).filter(is_read=False).update(is_read=True)

    @database_sync_to_async
    def update_thread_last_message(self, thread, message_text):
        thread.last_message = message_text
        thread.updated_at = datetime.now()
        thread.save()

    @database_sync_to_async
    def increment_thread_unread(self, thread, user):
        thread.increment_unread(user)

    @database_sync_to_async
    def get_thread_message_data(self, thread):
        messages = []
        for msg in thread.messages.all():
            try:
                user_profile = Profile.objects.get(user=msg.user)
                profile_pic_url = user_profile.profile_pic.url if user_profile.profile_pic else None
            except Exception:
                profile_pic_url = None
                
            # Format timestamp here instead of calling model method
            if hasattr(msg, 'timestamp'):
                timestamp_str = msg.timestamp.strftime("%b %d, %Y, %I:%M %p")
            else:
                timestamp_str = "Unknown time"
                
            messages.append({
                'id': msg.id,
                'message': msg.message,
                'user_id': msg.user.id,
                'username': msg.user.username,
                'timestamp': timestamp_str,
                'profile_pic': profile_pic_url,
                'is_read': msg.is_read
            })
        return messages

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            return Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return None

    @database_sync_to_async
    def get_unread_counts(self, user):
        threads = Thread.objects.by_user(user=user)
        unread_counts = {}
        for thread in threads:
            unread_counts[thread.id] = thread.get_unread_count(user)
        return unread_counts

    @database_sync_to_async
    def get_other_user(self, thread, user):
        """Safely get the other user in a thread"""
        if thread.first_person == user:
            return thread.second_person
        return thread.first_person

    @database_sync_to_async
    def check_user_in_thread(self, thread, user):
        """Check if a user is part of a thread"""
        return user == thread.first_person or user == thread.second_person
        
    @database_sync_to_async
    def get_thread_unread_count(self, thread, user):
        """Get the unread count for a user in a thread"""
        return thread.get_unread_count(user)
