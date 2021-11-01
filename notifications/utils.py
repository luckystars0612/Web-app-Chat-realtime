from datetime import datetime

from django.utils import timezone

from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturaltime

class LazyNotificationEncoder(Serializer):
    """
        Serialize a notification into a json
        3 types:
            1. FriendRequest
            2. FriendList
            3. UnreadChatRoomMessage
    """
    def get_dump_object(self, obj):
        dump_object = {}
        if obj.get_content_object_type()=="FriendRequest":
            dump_object.update({'notification_type': obj.get_content_object_type()}) #FriendList or FriendRequest
            dump_object.update({'notification_id': str(obj.id)})
            dump_object.update({'verb': str(obj.verb)})
            dump_object.update({'is_active': str(obj.content_object.is_active)})
            dump_object.update({'is_read': str(obj.is_read)})
            dump_object.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
            # print("\n")
            # print(obj.timestamp)
            # print(naturaltime(obj.timestamp))
            # print(timezone.now())
            # print(datetime.now())
            # print("\n")
            dump_object.update({'timestamp': str(obj.timestamp)})
            dump_object.update({
                'actions':{
                    'redirect_url':str(obj.redirect_url),

                },
                'from':{
                    'image_url':str(obj.from_user.profile_img.url)
                }
            })

        if obj.get_content_object_type() == "FriendList":
            dump_object.update({'notification_type': obj.get_content_object_type()})  # FriendList or FriendRequest
            dump_object.update({'notification_id': str(obj.id)})
            dump_object.update({'verb': str(obj.verb)})
            dump_object.update({'is_read': str(obj.is_read)})
            dump_object.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
            dump_object.update({'timestamp': str(obj.timestamp)})
            dump_object.update({
                'actions': {
                    'redirect_url': str(obj.redirect_url),

                },
                'from': {
                    'image_url': str(obj.from_user.profile_img.url),
                    # 'username':  str(obj.from_user.username),
                }
            })
        if obj.get_content_object_type() == "UnreadChatRoomMessages":
            dump_object.update({'notification_type': obj.get_content_object_type()})  # FriendList or FriendRequest
            dump_object.update({'notification_id': str(obj.id)})
            dump_object.update({'verb': str(obj.verb)})
            dump_object.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
            dump_object.update({'timestamp': str(obj.timestamp)})
            dump_object.update({
                'actions': {
                    'redirect_url': str(obj.redirect_url),

                },
                'from': {
                    'title':str(obj.content_object.get_other_user.username),
                    'image_url': str(obj.from_user.profile_img.url),
                    # 'username':  str(obj.from_user.username),
                }
            })

        return dump_object
