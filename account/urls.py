from . import views
from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [

    path('register/',views.Register,name='register'),
    path('login/',views.Login,name='login'),
    path('logout/',views.Logout,name='logout'),
    path('search/',views.search_view,name='search'),

    # Password reset links (ref: https://github.com/django/django/blob/master/django/contrib/auth/views.py)
    path('password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='account/password_reset/password_change_done.html'),
         name='password_change_done'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='account/password_reset/password_change.html'),
         name='password_change'),

    path('password_reset/done/', views.password_reset_done,name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset/password_reset_complete.html'),
         name='password_reset_complete'),
    path('<user_id>/',views.account_view,name='view'),
    path('<user_id>/edit/',views.edit_account,name='edit'),
]