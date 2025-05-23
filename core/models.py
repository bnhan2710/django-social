from cgitb import lookup
from statistics import mode
from turtle import update
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

# Create your models here.

User = get_user_model()


class Profile(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    userid = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(
        upload_to='profile_pics', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.CharField(max_length=100)
    image = models.ImageField(upload_to='posts', null=True, blank=True)  # Made optional
    music = models.FileField(upload_to='music', blank=True)
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(default=datetime.now)
    no_of_likes = models.IntegerField(default=0)

    def __str__(self):
        return self.user


class Comment(models.Model):
    user = models.CharField(max_length=100)
    post = models.ForeignKey(
        Post, related_name="comments", on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.user


class LikePost(models.Model):
    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class FollowersCount(models.Model):
    follower = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    def __str__(self):
        return self.follower


class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get('user')
        lookup = Q(first_person=user) | Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs

    def get_or_create(self, **kwargs):
        user = kwargs.get('user')
        receiver = kwargs.get('receiver')
        lookup1 = Q(first_person=user) & Q(second_person=receiver)
        lookup2 = Q(first_person=receiver) & Q(second_person=user)
        lookup = Q(lookup1 | lookup2)
        thread = self.get_queryset().filter(lookup)
        if thread.count() == 1:
            return thread.first(), False
        else:
            return Thread.objects.create(first_person=user, second_person=receiver), True


class Thread(models.Model):
    first_person = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='first_person')
    second_person = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='second_person')
    updated_at = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    unread_messages_count_first = models.IntegerField(default=0)
    unread_messages_count_second = models.IntegerField(default=0)
    last_message = models.TextField(blank=True, null=True)

    objects = ThreadManager()

    class Meta:
        unique_together = ['first_person', 'second_person']
        
    def get_other_user(self, user):
        """Return the other user in the thread"""
        if user == self.first_person:
            return self.second_person
        return self.first_person
    
    def mark_as_read(self, user):
        """Mark all messages as read for the given user"""
        if user == self.first_person:
            self.unread_messages_count_first = 0
        else:
            self.unread_messages_count_second = 0
        self.save()
    
    def increment_unread(self, user):
        """Increment unread count for the other user"""
        if user == self.first_person:
            self.unread_messages_count_second += 1
        else:
            self.unread_messages_count_first += 1
        self.save()
    
    def get_unread_count(self, user):
        """Get unread count for the given user"""
        if user == self.first_person:
            return self.unread_messages_count_first
        return self.unread_messages_count_second


class ChatMessage(models.Model):
    thread = models.ForeignKey(
        Thread, null=True, blank=True, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='messages_from')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']

    def get_timestamp(self):
        return self.timestamp.strftime('%I:%M %p')
        
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.save()

    def __str__(self):
        return self.message
