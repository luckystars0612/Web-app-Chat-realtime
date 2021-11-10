from datetime import datetime

from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.serializers.python import Serializer
from django.utils.html import escape

from chat.models import PrivateChatRoom
from chat.constants import *

def find_or_create_private_chat(user1,user2):
    try:
        chat = PrivateChatRoom.objects.get(user1=user1,user2=user2)
    except PrivateChatRoom.DoesNotExist:
        try:
            chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
        except Exception as e:
            chat = PrivateChatRoom(user1=user1,user2=user2)
            chat.save()
    return chat

def calculate_timestamp(timestamp):
    """
        1. today or yesterday:
        ex: today at 10:00pm
        2. other
        ex: 15/10/2021 at 10:00pm
    """
    #today or yesterday
    if ((naturalday(timestamp)=="today") or (naturalday(timestamp)=="yesterday")):
        str_time = datetime.strftime(timestamp,"%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    #other day
    else:
        str_day = datetime.strftime(timestamp,"%d/%m/%Y")
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{str_day} at {str_time}"
    return ts

class LazyRoomChatMessageEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
        dump_object.update({'msg_id': str(obj.id)})
        dump_object.update({'user_id': str(obj.user.id)})
        dump_object.update({'username': str(obj.user.username)})
        dump_object.update({'message': escape(str(obj.content))})
        dump_object.update({'profile_img': str(obj.user.profile_img.url)})
        dump_object.update({'timestamp': calculate_timestamp(obj.timestamp)})
        if (obj.file):
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            dump_object.update({'file': obj.file.url})

        return dump_object