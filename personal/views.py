
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from chat.views import get_recent_chatroom_messages
from public_chat.models import PublicRoomChatMessage, PublicChatRoom


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
    room = PublicChatRoom.objects.first()
    newMessage = PublicRoomChatMessage(user=request.user, room=room, content=file.name, file=file)
    newMessage.save()
    print('-'*50)
    print(file)
    print('-'*50)
    return redirect(reverse('public-chat'))


