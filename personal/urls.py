
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.home_screen_view,name='public-chat'),
    path('upload/',views.upload_file,name='upload-file'),
]