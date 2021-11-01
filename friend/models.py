import datetime

from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.

from chat.utils import find_or_create_private_chat
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from django.db.models.signals import post_save
from django.dispatch import receiver

class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="user")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friends")

    #for reverse lookup
    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.user.username

    def add_friend(self,account):
        if not account in self.friends.all():
            self.friends.add(account)
            self.save()
            content_type = ContentType.objects.get_for_model(self)
            #create notification
            # Notification(
            #     target=self.user,
            #     from_user=account,
            #     redirect_url=f"{settings.BASE_URL}/account/{account.pk}/",
            #     verb=f"You are now friend with {account.username}",
            #     content_type=content_type,
            #     object_id=self.id
            # ).save()

            self.notifications.create(
                target=self.user,
                from_user=account,
                redirect_url=f"{settings.BASE_URL}/account/{account.pk}/",
                verb=f"You are now friend with {account.username}",
                content_type=content_type,
            )
            self.save()
            #create private chat or active an old one
            chat = find_or_create_private_chat(self.user, account)
            if not chat.is_active:
                chat.is_active = True
                chat.save()

    def remove_friend(self,account):
        if account in self.friends.all():
            self.friends.remove(account)
            chat = find_or_create_private_chat(self.user, account)
            if chat.is_active:
                chat.is_active = False
                chat.save()

    def unfriend(self,removee):
        """
            Initiate the action of unfriending someone
            remover is the person who execute the unfriend action
            removee is the person who is unfriended
        """
        remover_friends_list = self

        #remove friend from the remover friend list
        remover_friends_list.remove_friend(removee)

        #remove friend from removee friend list
        removee_friends_list = FriendList.objects.get(user=removee)
        removee_friends_list.remove_friend(self.user) # delete myself from removee friend list


        content_type = ContentType.objects.get_for_model(self)

        # create notification for removee
        self.notifications.create(
            target=removee,
            from_user=self.user,
            redirect_url=f"{settings.BASE_URL}/account/{self.user.pk}/",
            verb=f"You are no longer friend with {self.user.username}",
            content_type=content_type,
        )
        self.save()

        #create notification for remover
        self.notifications.create(
            target=self.user,
            from_user=removee,
            redirect_url=f"{settings.BASE_URL}/account/{removee.pk}/",
            verb=f"You are no longer friend with {removee.username}",
            content_type=content_type,
        )
        self.save()

    def is_friend(self, friend):
        if friend in self.friends.all():
            return True
        return False

    @property
    def get_cname(self):
        #determine what kind of object is associated with a Notification
        return "FriendList"

class FriendRequest(models.Model):
    """
        two parts:
        sender: who send friend request
        receiver: who receive friend request
    """
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receiver")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.sender.username

    def accept(self):
        """
            if accept a friend request then update both sender and receiver friend lists
        """
        receiver_friend_list = FriendList.objects.get(user=self.receiver)
        if receiver_friend_list:
            content_type = ContentType.objects.get_for_model(self)
            #update notification for receiver
            receiver_notification = Notification.objects.get(
                target=self.receiver,content_type=content_type,object_id=self.id)

            receiver_notification.is_active = False
            receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.pk}"
            receiver_notification.verb = f"You accepted {self.sender.username}'s friend request"
            receiver_notification.timestamp = timezone.now()
            receiver_notification.save()

            receiver_friend_list.add_friend(self.sender)
            sender_friend_list = FriendList.objects.get(user=self.sender)

            if sender_friend_list:

                #create notifcation for sender
                self.notifications.create(
                    target=self.sender,
                    from_user=self.receiver,
                    redirect_url=f"{settings.BASE_URL}/account/{self.receiver.pk}/",
                    verb=f"{self.receiver.username} accepted your friend request",
                    content_type=content_type,
                )
                sender_friend_list.add_friend(self.receiver)
                self.is_active = False
                self.save()
            return receiver_notification

    def decline(self):
        """
            decline a friend request
            decline by setting is_active to false
        """
        self.is_active = False
        self.save()

        content_type = ContentType.objects.get_for_model(self)

        # update notification for receiver
        receiver_notification = Notification.objects.get(
            target=self.receiver, content_type=content_type, object_id=self.id)

        receiver_notification.is_active = False
        receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.pk}"
        receiver_notification.verb = f"You declined {self.sender.username}'s friend request"
        receiver_notification.timestamp = timezone.now()
        receiver_notification.save()

        # create notification for sender
        self.notifications.create(
            target=self.sender,
            from_user=self.receiver,
            redirect_url=f"{settings.BASE_URL}/account/{self.receiver.pk}/",
            verb=f"{self.receiver.username} declined your friend request",
            content_type=content_type,
        )

        return receiver_notification

    def cancel(self):
        """
            same as decline, just different in notifications
        """
        self.is_active = False
        self.save()

    @property
    def get_cname(self):
        # determine what kind of object is associated with a Notification
        return "FriendRequest"

@receiver(post_save,sender=FriendRequest)
def create_notification(sender,instance,created,**kwargs):
    if created:
        instance.notifications.create(
            target=instance.receiver,
            from_user=instance.sender,
            redirect_url=f"{settings.BASE_URL}/account/{instance.sender.pk}/",
            verb=f"{instance.sender.username} sent you a friend request",
            content_type=instance,
        )