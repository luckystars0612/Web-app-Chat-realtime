from django.core.serializers.python import Serializer

class LazyAccountEncoder(Serializer):

    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'id':str(obj.id)})
        dump_object.update({'email': str(obj.email)})
        dump_object.update({'username': str(obj.username)})
        dump_object.update({'profile_img': str(obj.profile_img.url)})
        dump_object.update({'is_online': str(obj.is_online)})
        return dump_object
