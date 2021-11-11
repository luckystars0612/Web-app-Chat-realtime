from django.urls import path

from .views import *

app_name = "chat"

urlpatterns = [
    path("",private_chatroom_view,name="private-chat"),
    path("create_private_chat/",create_or_return_private_chat,name="create_or_return_private_chat"),
    path("call/",VideoCall,name='video-call')
]