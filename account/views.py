
from django.shortcuts import render,redirect
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout

from ChatApp import settings
from friend.friend_request_status import FriendRequestStatus
from friend.models import FriendList, FriendRequest
from .forms import RegistrationForm,AccountAuthenticationForm,AccountUpdateForm
from .models import Account
from ChatApp.settings import BASE_URL
from django.db.models import Q
from friend.utils import get_friend_request_or_false
# Create your views here.

from PIL import Image

def Register(request):

    context={}
    user = request.user

    if user.is_authenticated:
        # return HttpResponse(f"You are already authenticated as {user.email}")
        return redirect("home")

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email,password=raw_password)
            login(request,account)
            destination = get_redirect_if_exists(request)
            if destination:
                return redirect(destination)
            return redirect("home")
        else:
            context['registration_form']= form
    return render(request, "account/register.html", context)

def Login(request):

    context={}
    user = request.user

    if user.is_authenticated:
        return redirect("home")

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email,password=password)
            if user:
                login(request,user)
                destination = get_redirect_if_exists(request)
                if destination:
                    return redirect(destination)
                return redirect("home")
        else:
                context['login_form']=form
    return render(request,"account/login.html",context)
def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("next"))
    return redirect

def Logout(request):
    logout(request)
    return redirect("home")

def password_reset_done(request):
    return render(request,"account/password_reset/password_reset_done.html")

def account_view(request, **kwargs):
    '''
        logic:
        is_self(bool):
            is_friend(bool):
                -1: NO_REQUEST_SENT
                0: THEM_SENT_TO_YOU
                1: YOU_SENT_TO_THEM
    '''
    context={}
    user_id=kwargs.get("user_id")
    try:
        account=Account.objects.get(pk=user_id)
    except:
        return HttpResponse("User doesn't exist")
    if account:
        context['id']=account.id
        context['username']=account.username
        context['email'] = account.email
        context['profile_image']=account.profile_img.url
        context['hide_email']=account.hide_email

        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()
        friends = friend_list.friends.all()
        context['friends'] = friends

        #define state variables
        is_self = True
        is_friend = False
        user = request.user
        request_sent = None
        friend_requests = None
        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                #case1: someone sent friend request for you
                #FriendRequestStatus.THEM_SENT_TO_YOU
                if get_friend_request_or_false(sender=account,receiver=user) != False:
                    if get_friend_request_or_false(sender=account,receiver=user).is_active==True:
                        request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                        context['pending_friend_request_id'] = get_friend_request_or_false(sender=account,
                                                                                           receiver=user).id
                    else:
                        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
                #case2: you send someone a friend request:
                elif get_friend_request_or_false(sender=user,receiver=account) != False:
                    if get_friend_request_or_false(sender=user,receiver=account).is_active==True:
                        request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                    else:
                        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
                #case3: no request sent
                else :
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                friend_requests = FriendRequest.objects.filter(receiver=user,is_active=True)
            except:
                pass
        context['is_self']=is_self
        context['is_friend']=is_friend
        context['BASE_URL']= BASE_URL
        context['request_sent']=request_sent
        context['friend_requests'] = friend_requests
        return render(request,"account/account.html",context)

def search_view(request, **kwargs):
    context={}
    user = request.user
    if request.method=="GET":
        search_query = request.GET.get("keyword")
        print(search_query)
        if len(search_query) > 0:
            search_results = Account.objects.all().filter(Q(email__icontains=search_query) or Q(username__icontains=search_query))
            accounts=[]
            if user.is_authenticated:
                #get authenticated user friend list
                try:
                    auth_user_friend_list = FriendList.objects.get(user=user)
                except FriendList.DoesNotExist:
                    auth_user_friend_list = FriendList(user=user)
                    auth_user_friend_list.save()
                for account in search_results:
                    accounts.append((account,auth_user_friend_list.is_friend(account)))
                context['accounts'] = accounts
            else:
                for account in search_results:
                    accounts.append((account,False))
                context['accounts'] = accounts
    return render(request,"account/search_results.html",context)

def edit_account(request, **kwargs):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id=kwargs.get('user_id')
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        raise HttpResponse("Something went wrong")
    if account.pk != request.user.pk:
        return HttpResponse("You can't edit someone's profile")
    context={}
    if request.POST:
        form = AccountUpdateForm(request.POST,request.FILES,instance=request.user)
        account = Account.objects.get(pk=request.user.pk)
        print(account.profile_img.url)
        if form.is_valid():
            #delete old image

            account.profile_img.delete()
            form.save()
            return redirect("view", user_id=account.pk)
        else:
            initial_list = {
                "id": account.pk,
                "email": account.email,
                "username": account.username,
                "profile_img": account.profile_img,
                "hide_email": account.hide_email
            }
            form = AccountUpdateForm(request.POST,instance=request.user,initial=initial_list)
            context['form'] = form
    else:
        initial_list={
            "id": account.pk,
            "email": account.email,
            "username": account.username,
            "profile_img": account.profile_img,
            "hide_email": account.hide_email
        }
        form = AccountUpdateForm(initial=initial_list)
        context['form'] = form
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request,"account/edit_account.html",context)