
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from chat.views import get_recent_chatroom_messages
from public_chat.models import PublicRoomChatMessage, PublicChatRoom
from chat.models import RoomChatMessage, PrivateChatRoom


DEBUG = False
def home_screen_view(request):

    context = {}
    context['debug_mode'] = settings.DEBUG
    context['debug'] = DEBUG
    context['room_id'] = 1
    context['auth_user_id'] = request.user.id
    context['base_url'] = settings.BASE_URL

    user = request.user
    if not user.is_authenticated:
        return redirect("login")

    context['m_and_f'] = get_recent_chatroom_messages(user)

    return render(request,"personal/home.html",context)


def upload_file(request):
    file = request.FILES['file']
    try:
        room = request.POST['room']
        room_id = request.POST['room_id']
    except:
        pass

    print('a'*50, room)
    if room == "private":
        private_room = PrivateChatRoom.objects.get(id=room_id)
        newMessage = RoomChatMessage(user=request.user, room=private_room, content=file.name, file=file)
    else:
        room = PublicChatRoom.objects.first()
        newMessage = PublicRoomChatMessage(user=request.user, room=room, content=file.name, file=file)
    newMessage.save()
    return JsonResponse(status=201, data= {
        "file": newMessage.file.url,
        "content": newMessage.content
    })
    



