import datetime
from itertools import chain

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.core.serializers import serialize
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.html import escape
import requests
import threading

import json
import asyncio

from chat.exceptions import ClientError
from chat.models import RoomChatMessage, PrivateChatRoom, UnreadChatRoomMessages
from friend.models import FriendList
from account.utils import LazyAccountEncoder
from chat.utils import calculate_timestamp,LazyRoomChatMessageEncoder
from chat.constants import *
from account.models import Account
from chat.views import get_recent_chatroom_messages


class ChatConsumer(AsyncJsonWebsocketConsumer):

    @database_sync_to_async
    def isBot(self, room_id):
        return str(PrivateChatRoom.objects.get(id=room_id).user1) == 'bot'

    async def connect(self):
        print("ChatConsumer: connect"+str(self.scope['user']))
        await self.accept()
        self.room_id = None

    async def receive_json(self, content, **kwargs):
        """
        	Called when we get a text frame. Channels will JSON-decode the payload
        	for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        print("ChatConsumer: receive_json")
        file = content.get("file", None)
        command = content.get("command", None)
        try:
            if command == "join":
                print("joining room: " + str(content['room']))
                await self.join_room(content['room'])

            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422,"You can not send a empty message")
                await self.send_room_message(content['room'],content['message'], file)
                isBot = await self.isBot(content['room'])
                if isBot:
                    await self.talk_with_bot(content['room'],content['message'])
                # if len(content['message'].lstrip()) != 0:
                #     await self.send_room_message(content['room'], self.scope['user'])
            elif command == "get_room_chat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'],self.scope['user'])
                payload = await get_room_chat_messages(room,content['page_number'])
                if payload != None:
                    payload=json.loads(payload)
                    await self.send_messages_payload(payload['messages'],payload['new_page_number'])
                else:
                    raise ClientError(204,"Retrieve room message fail")
                await self.display_progress_bar(False)
            elif command == "get_user_info":
                room = await get_room_or_error(content['room_id'],self.scope['user'])
                payload = get_user_info(room,self.scope['user'])
                if payload != None:
                    payload = json.loads(payload)
                    await self.send_user_info_payload(payload['user_info'])
                else:
                    raise ClientError("INVALID_PAYLOAD","Retrieve user info fail")
            elif command == "get_friends_info":
                print("ChatConsumer: get friends info")
                payload = await get_friends_info(self.scope['user'])
                if payload != None:
                    payload = json.loads(payload)
                    await self.send_user_friend_info(payload['friends_info'])
                else:
                    raise ClientError("INVALID_PAYLOAD","Retrieve friend's user info fail")
        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the room
        print("ChatConsumer: disconnect")
        try:
            if self.room_id != None:
                await self.leave_room(self.room_id)
        except Exception as e:
            pass

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
        print("ChatConsumer: join_room: " + str(room_id))
        try:
            room = await get_room_or_error(room_id,self.scope['user'])
        except ClientError as e:
            return await self.handle_client_error(e)

        await connect_user(room,self.scope['user'])

        #Store that we're in the room
        self.room_id = room_id

        await on_user_connected(room,self.scope['user'])

        #add them to the group, so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )

        await self.send_json({
            "join":str(room_id)
        })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        print("ChatConsumer: leave_room")

        room = await get_room_or_error(room_id,self.scope['user'])

        await disconnect_user(room,self.scope['user'])

        #Notify the group that someone left
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type":"chat.leave",
                "room_id": room_id,
                "profile_img": self.scope['user'].profile_img.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,

            }
        )

        self.room_id = None

        #remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )

        await self.send_json({
            "leave":str(room.id)
        })

    async def send_room_message(self, room_id, message, file=None):
        """
        Called by receive_json when someone sends a message to a room.
        """
        print("ChatConsumer: send_room_message")
        if self.room_id != None:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS_DENIED","room access denied")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "room access denied")

        room = await get_room_or_error(room_id,self.scope['user'])

        connected_users = room.connected_users.all()

        await asyncio.gather(*[
            append_unread_msg_if_not_connected(room, room.user2, connected_users, message),
            append_unread_msg_if_not_connected(room, room.user1, connected_users, message),
            #create_room_chat_message(room, self.scope['user'], message)

        ])

        dataJson = {
            "type":"chat.message",
            "profile_img":self.scope['user'].profile_img.url,
            "username":self.scope['user'].username,
            "user_id":self.scope['user'].id,
            "message":message,
        }

        if not file:
            await create_room_chat_message(room, self.scope['user'], message)
        else:
            dataJson['file'] = file

        await self.channel_layer.group_send(
            room.group_name, dataJson
        )
    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        print("ChatConsumer: chat_join: " + str(self.scope["user"].id))
        pass

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        print("ChatConsumer: chat_leave")
        pass

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        print("ChatConsumer: chat_message")

        timestamp = calculate_timestamp(datetime.datetime.now())
        dataJson = {
            "msg_type": MSG_TYPE_MESSAGE,
            "profile_img": event['profile_img'],
            "username": event['username'],
            "user_id":event['user_id'],
            "message": escape(event['message']),
            "timestamp":timestamp,
        }
        try:
            dataJson['file'] = escape(event['file'])
        except: pass
        
        await self.send_json(dataJson)

    async def send_messages_payload(self, messages, new_page_number):
        """
        Send a payload of messages to the ui
        """
        print("ChatConsumer: send_messages_payload. ")

        await self.send_json({
            "messages_payload":"messages_payload",
            "messages":messages,
            "new_page_number":new_page_number,
        })

    async def send_user_info_payload(self, user_info):
        """
        Send a payload of user information to the ui
        """
        print("ChatConsumer: send_user_info_payload. ")

        await self.send_json({
            'user_info':user_info
        })

    async def send_user_friend_info(self,friends_info):
        print("ChatConsumer: send_friends_info")

        await self.send_json({
            'friends_info': friends_info
        })

    async def display_progress_bar(self, is_displayed):
        """
        1. is_displayed = True
        - Display the progress bar on UI
        2. is_displayed = False
        - Hide the progress bar on UI
        """
        print("DISPLAY PROGRESS BAR: "+str(is_displayed))
        await self.send_json({
            "display_progress_bar":is_displayed,
        })


    async def handle_client_error(self,error):
        """
            Called when ClientError is raised.
            Send errror data to UI
        """
        errorData ={}
        errorData['error'] = error.code
        if error.messsage:
            errorData['message'] = error.messsage
            await self.send_json(errorData)
        return


    async def talk_with_bot(self, room_id, message):
        res = requests.get(f'https://api.simsimi.net/v2/?text={message}&lc=vn').json()
        room = await get_room_or_error(room_id,self.scope['user'])
        dataJson = {
            "type":"chat.message",
            "profile_img":room.user1.profile_img.url,
            "username":room.user1.username,
            "user_id":room.user1.id,
            "message":res['success'],
        }
        await self.channel_layer.group_send(
            room.group_name, dataJson
        )

        await create_room_chat_message(room, room.user1, res['success'])




@database_sync_to_async
def get_bot_account():
    return Account.objects.get(username='bot')

@database_sync_to_async
def get_room_or_error(room_id,user):
    """
        Try to fetch a room for the user, check permissions along the way
    """
    try:
        room = PrivateChatRoom.objects.get(pk=room_id)

    except PrivateChatRoom.DoesNotExist:
        raise ClientError("INVALID_ROOM","Invalid room")

    #check if user is allowed to access this room
    if user != room.user1 and user != room.user2:
        raise ClientError("ROOM_ACCESS_DENIED","You do not have permission to join this room")

    #are the users in this room friends
    friend_list = FriendList.objects.get(user=user).friends.all()
    if not room.user1 in friend_list:
        if not room.user2 in friend_list:
            raise ClientError("ROOM_ACCESS_DENIED","You must be friend to chat")
    return room

def get_user_info(room,user):
    """
        return user info for the user who you are chatting with
    """
    try:
        other_user = room.user1
        if other_user == user:
            other_user = room.user2
        payload = {}
        s = LazyAccountEncoder()
        payload['user_info'] = s.serialize([other_user])[0]
        return json.dumps(payload)
    except ClientError as e:
        print("Exception: "+str(e))
    return None

@database_sync_to_async
def get_friends_info(user):
    """
        return friends info of the authenticated user
    """
    try:
        friend_list = FriendList.objects.get(user=user)
        friends = friend_list.friends.all()
        payload = {}
        s = LazyAccountEncoder()
        payload['friends_info'] = s.serialize(friends)
        newest_msg_list = get_recent_chatroom_messages(user)

        for data in payload['friends_info']:
            for msg in newest_msg_list:
                if data['id'] == str(msg['friend'].id):
                    data['newest_message'] = escape(msg['message'].content)
            #print(data)
        return json.dumps(payload)

    except FriendList.DoesNotExist:
        pass
    return None

@database_sync_to_async
def create_room_chat_message(room,user,message):
    return RoomChatMessage.objects.create(user=user,room=room,content=message)

@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = RoomChatMessage.objects.by_room(room)
        p = Paginator(qs,DEFAULT_ROOMCHAT_MESSAGES_PAGE_SIZE)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number+=1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = None

        payload['new_page_number'] = new_page_number
        return json.dumps(payload)

    except Exception as e:
        print("Exception: "+str(e))
    return None

@database_sync_to_async
def connect_user(room, user):
    # add user to connected_users list
    account = Account.objects.get(pk=user.id)
    return room.connect_user(account)


@database_sync_to_async
def disconnect_user(room, user):
    # remove from connected_users list
    account = Account.objects.get(pk=user.id)
    return room.disconnect_user(account)


# If the user is not connected to the chat, increment "unread messages" count
@database_sync_to_async
def append_unread_msg_if_not_connected(room, user, connected_users, message):
    if not user in connected_users:
        try:
            unread_msgs = UnreadChatRoomMessages.objects.get(room=room, user=user)
            unread_msgs.most_recent_message = message
            unread_msgs.count += 1
            unread_msgs.save()
        except UnreadChatRoomMessages.DoesNotExist:
            UnreadChatRoomMessages(room=room, user=user, count=1).save()
            pass
    return

# When a user connects, reset their unread message count
@database_sync_to_async
def on_user_connected(room, user):
    # confirm they are in the connected users list
    connected_users = room.connected_users.all()
    if user in connected_users:
        try:
            # reset count
            unread_msgs = UnreadChatRoomMessages.objects.get(room=room, user=user)
            unread_msgs.count = 0
            unread_msgs.save()
        except UnreadChatRoomMessages.DoesNotExist:
            UnreadChatRoomMessages(room=room, user=user).save()
            pass
    return