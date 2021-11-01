from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
from account.models import Account
from friend.models import FriendRequest,FriendList
# Create your views here.

def send_friend_request(request, **kwargs):
    user = request.user
    payload ={}
    if request.method=="POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                #get any friends request
                friend_request = FriendRequest.objects.get(sender=user,receiver=receiver)
                print(friend_request)
                #find if any of them are active
                if friend_request.is_active:
                    raise Exception("You already sent them a friend request")
                else:
                    friend_request.is_active = True
                    friend_request.save()
                payload['response'] = "Friend request sent"

            except FriendRequest.DoesNotExist:
                #there are no friend requests so create one
                friend_request = FriendRequest(sender=user,receiver=receiver)
                friend_request.save()
                payload['response'] = "Friend request sent"

            if payload['response'] == None:
                payload['response'] = "Something went wrong"
        else:
            payload['response'] = "Unable to send a friend request"
    else:
        payload['response'] = "You must be authenticated to send request"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def accept_friend_request(request, **kwargs):
    user = request.user
    payload={}
    if request.method=="GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            #confirm that is the correct request:
            if friend_request.receiver==user:
                if friend_request:
                    friend_request.accept()
                    payload['response']="Friend request accepted"
                else:
                    payload['response'] = "Something went wrong"
            else:
                payload['response'] = "This is not your request"
        else:
            payload['response'] = "Unable to accept this request"
    else:
        payload['response'] = "You must be authenticated"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def remove_friend(request, **kwargs):
    user =  request.user
    payload={}
    if request.method=="POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            try:
                removee = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                payload['response'] = "Succesfully removed friend"
            except Exception as e:
                payload['response'] = "Something went wrong:"+ str(e)
        else:
            payload['response'] = "Error. Unable to remove this friend"
    else:
        payload['response']  = "You must be authenticate first"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def decline_friend_request(request, **kwargs):
    user = request.user
    payload={}
    if request.method=="GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            #confirm it's correct request
            if friend_request.receiver==user:
                if friend_request:
                    friend_request.decline()
                    payload['response']="Request is declined"
                else:
                    payload['response'] = "Something went wrong"
            else:
                payload['response'] = "That is not your friend request"
        else:
            payload['response'] = "Unable to decline that friend request"
    else:
        payload['response'] = "You must be authenticated"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def cancel_friend_request(request,**kwargs):
    user = request.user
    payload={}
    if request.method=="POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver =  Account.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user,receiver=receiver)
            except Exception as e:
                payload['response'] = "Friend request does not exist"
            if len(friend_requests)>1:
                for request in friend_requests:
                    request.cancel()
                payload['response'] = "Friend request canceled"
            else:
                friend_requests.first().cancel()
                payload['response'] = "Friend request canceled"
        else:
            payload['response'] = "Unable to cancel this friend request"
    else:
        payload['response'] = "You must be authenticated"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def friend_requests_view(request, **kwargs):
    context={}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        account = Account.objects.get(pk=user_id)
        if user == account:
            friend_requests = FriendRequest.objects.filter(receiver=account,is_active=True)
            context['friend_requests'] = friend_requests
        else:
            return HttpResponse("You can't view another users friend requests")
    else:
        redirect("login")
    return render(request,"friend/friend_requests.html",context)

def friend_list_view(request,**kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        if user_id:
            try:
                this_user = Account.objects.get(pk=user_id)
                context['this_user']=this_user
            except Account.DoesNotExist:
                return HttpResponse("User does not exist")
            try:
                friend_list = FriendList.objects.get(user=this_user)
            except FriendList.DoesNotExist:
                return HttpResponse(f"cound not file friends list for {this_user.username}")

            #must be friend to view friend list
            if user != this_user:
                if not user in friend_list.friends.all():
                    return HttpResponse("You must be friend to view other friend list")
            friends=[]
            auth_user_friend_list = FriendList.objects.get(user=user)
            for friend in friend_list.friends.all():
                friends.append((friend,auth_user_friend_list.is_friend(friend)))
            context['friends'] = friends
    else:
        return HttpResponse("You must be authenticated")
    return render(request,"friend/friend_list.html",context)





