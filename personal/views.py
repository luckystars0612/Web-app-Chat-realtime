
from django.shortcuts import render, redirect
from django.conf import settings
from chat.views import get_recent_chatroom_messages


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



