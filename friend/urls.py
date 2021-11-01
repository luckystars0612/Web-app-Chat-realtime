
from django.urls import path, include
from . import views

app_name="friend"
urlpatterns = [
    path('friendlist/<user_id>/', views.friend_list_view, name="list"),
    path('friend_request', views.send_friend_request, name="friend-request"),
    path('friend_request/<user_id>/', views.friend_requests_view, name="friend-requests"),
    path('accept_friend_request/<friend_request_id>/', views.accept_friend_request, name="friend-request-accept"),
    path('friend_remove/', views.remove_friend, name="remove-friend"),
    path('decline_friend_request/<friend_request_id>/', views.decline_friend_request, name="friend-request-decline"),
    path('cancel_friend_request/', views.cancel_friend_request, name="friend-request-cancel"),
]

