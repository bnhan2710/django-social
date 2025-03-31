from cgitb import lookup
from django.contrib import admin
from django.db.models import Q
from django.core.exceptions import ValidationError
from django import forms
from .models import Profile, Post, LikePost, FollowersCount, Comment, Thread, ChatMessage

# Register your models here.

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(LikePost)
admin.site.register(FollowersCount)
admin.site.register(Comment)
admin.site.register(Thread)
admin.site.register(ChatMessage)


class ChatMessage(admin.TabularInline):
    model = ChatMessage


class ThreadAdmin(admin.ModelAdmin):
    inlines = [ChatMessage]

    class Meta:
        model = Thread
