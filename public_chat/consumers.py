from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime
from public_chat.models import PublicChatRoom,PublicRoomChatMessage
from channels.db import database_sync_to_async
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.core.serializers import serialize
from .constants import *
from chat.utils import calculate_timestamp
from chat.exceptions import ClientError
from django.utils.html import escape

User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """
            Called when the websocket is handshaking as part of initial connection
        """
        print("PublicChatConsumer: connect: "+ str(self.scope['user']))
        await self.accept()
        self.room_id = None
        #add them to the group so they get room messages
        # await self.channel_layer.group_add(
        #     "public_chatroom_2",
        #     self.channel_name
        # )
    async def disconnect(self, code):
        """
        Called when the websocket closes
        """
        print("PublicChatConsumer : disconnect")
        try:
            if self.room_id != None:
                await self.leave_room(self.room_id)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        """
            Called when we get a text frame. Channels will JSON decode the payload for us and pass
            it as the first argument
        """
        command = content.get("command",None)
        message = content.get("message",None)
        print("PublicChatConsumer: receive_json: "+str(command))
        print("PublicChatConsumer: receive_json: " + str(message))
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422,"You can't send an empty message")
                await self.send_room_message(content['room_id'],content['message'])
            elif command == "join":
                await self.join_room(content['room'])
            elif command == "leave":
                await self.leave_room((content['room']))
            elif command == "get_roomchat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'])
                payload = await get_roomchat_messages(room,content['page_number'])
                if payload != None:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204,"Something went wrong retrieving chatroom messages")
                await self.display_progress_bar(False)
        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)
        pass

    async def send_room_message(self, room_id, message):
        """
            called by receive_json when someone sends a message to a room
        """
        print("PublicChatConsumer: send_message_room")

        if self.room_id != None:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS_DENIED","Room access denied")
            if not is_authenticated(self.scope['user']):
                raise ClientError("AUTH_ERROR","you must be authenticated to chat")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")

        room = await get_room_or_error(room_id)

        await create_public_room_chat_message(room, self.scope['user'], message)

        await self.channel_layer.group_send(
            room.group_name,
            {
                "type":"chat.message", #chat_message()
                'profile_img': self.scope['user'].profile_img.url,
                'username': self.scope['user'].username,
                'user_id': self.scope['user'].id,
                'message': message,
            }
        )
    async def chat_message(self,event):
        """
            Called when someone has messaged our chat
        """
        #sent a message down to client
        print("PublicChatConsumer: chat_message from user #:"+str(event['user_id']))
        timestamp = calculate_timestamp(datetime.now())
        await self.send_json({
            "msg_type": MSG_TYPE_MESSAGE,
            "profile_img": event['profile_img'],
            "username": event['username'],
            "user_id":event['user_id'],
            "message": escape(event['message']),
            "timestamp":timestamp,
        })

    async def join_room(self,room_id):
        """
            Called by receive_json when someone send a JOIN command
        """

        print("PublicChatComsumer: join_room")

        is_auth =  is_authenticated(self.scope['user'])

        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)
        #add user to the users list of room
        if is_auth:
            await connect_user(room,self.scope['user'])
        #store that we're the room
        self.room_id = room.id

        #add them to the group to get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )
        #tell the client to finish opening the room
        await self.send_json({
            "join": str(room_id),
            "username": self.scope['user'].username,
        })

        # send the number of connected user for client
        number_connected_user = await get_number_connected_users(room)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type":"connected.user.count",
                "connected_user_count":number_connected_user,
            }
        )

    async def leave_room(self,room_id):
        """
            called by receive_json when someone sent a LEAVE command
        """
        print("PublicChatConsumer: leave_room")
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)

        #remove user from users list of the room
        if is_auth:
            await disconnect_user(room, self.scope['user'])
        #remove that we're in the room
        self.room_id = None
        #Remove them from the group so they no longer receive messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )

        # send the number of connected user for client
        number_connected_user = await get_number_connected_users(room)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "connected.user.count",
                "connected_user_count": number_connected_user,
            }
        )


    async def send_messages_payload(self,messages, new_page_number):
        """
            Sends a payload of messages to UI
        """
        print("PublicChatConsumer: send_messages_payload")
        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number,
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

    async def display_progress_bar(self,is_displayed):
        """
            1. is_displayed =true
             - display the progress bar on UI
            2. is_displayed = false
             - hide the progress bar on UI
        """
        print("DISPLAY PROGRESS BAR"+str(is_displayed))
        await self.send_json({
            "display_progress_bar": is_displayed
        })

    async def connected_user_count(self,event):
        """
            Called to send the number of users connected to the room
        """
        print("PublicChatConsumer: connected_user_count: "+ str(event['connected_user_count']))
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
            "connected_user_count": event['connected_user_count'],
        })

@database_sync_to_async
def get_number_connected_users(room):
    if room.users:
        return len(room.users.all())
    return 0

def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False

@database_sync_to_async
def create_public_room_chat_message(room,user,message):
    return PublicRoomChatMessage.objects.create(user=user,room=room,content=message)

@database_sync_to_async
def connect_user(room,user):
    return room.connect_user(user)

@database_sync_to_async
def disconnect_user(room,user):
    return room.disconnect_user(user)

@database_sync_to_async
def get_room_or_error(room_id):
    """
        Fetch room for the user
    """
    try:
        room = PublicChatRoom.objects.get(pk=room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError("ROOM_INVALID","Invalid room")
    return room


@database_sync_to_async
def get_roomchat_messages(room,page_number):
    try:
        query_set = PublicRoomChatMessage.objects.by_room(room)
        print("-"*50)
        print(query_set)
        print("-"*50)

        p = Paginator(query_set, DEFAULT_ROOMCHAT_MESSAGES_PAGE_SIZE)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = "None"

        payload['new_page_number'] = new_page_number

        return json.dumps(payload)
    except Exception as e:
        print("EXCEPTION: "+str(e))
        return None


class LazyRoomChatMessageEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_type':MSG_TYPE_MESSAGE})
        dump_object.update({'user_id': str(obj.user.id)})
        dump_object.update({'username': str(obj.user.username)})
        dump_object.update({'message': str(obj.content)})
        dump_object.update({'profile_img': str(obj.user.profile_img.url)})
        dump_object.update({'timestamp': calculate_timestamp(obj.timestamp)})
        if (obj.file):
            dump_object.update({'file': obj.file.url})
        return dump_object
