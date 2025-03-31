from asyncio import threads
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from matplotlib import image
from pip import main
from requests import post
from .models import Profile, Post, LikePost, FollowersCount, Comment, Thread, ChatMessage
from itertools import chain
import random
# Create your views here.


@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    posts = Post.objects.all().order_by('-created_at')
    # for post in posts:
    #     user_obj = User.objects.get(username=post.user)
    #     post.img = Profile.objects.get(user=user_obj).profile_pic.url

    user_following_list = [user_object]
    feed = []

    user_following = FollowersCount.objects.filter(
        follower=request.user.username)
    for user in user_following:
        user_following_list.append(user.user)

    for username in user_following_list:
        feed_lists = Post.objects.filter(user=username)
        for feed_list in feed_lists:
            feed_list.post_comments = Comment.objects.filter(
                post=feed_list).order_by('-created_at')[0:3]
            feed_list.count_comments = Comment.objects.filter(
                post=feed_list).count()
            user_obj = User.objects.get(username=feed_list.user)
            feed_list.img = Profile.objects.get(user=user_obj).profile_pic.url
        feed.append(feed_lists)

    # feed.sort(key=lambda x: x.created_at, reverse=False)
    feed = list(chain(*feed))
    # sort feed by created_at
    feed.sort(key=lambda x: x.created_at, reverse=True)

    # user suggestions start
    all_users = User.objects.all()
    user_following_all = []
    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)
    # print(user_following_all)

    new_suggestions_list = [x for x in list(
        all_users) if x not in user_following_all]
    current_user = User.objects.filter(username=request.user.username)
    new_suggestions_list = [
        x for x in new_suggestions_list if x not in current_user]
    random.shuffle(new_suggestions_list)

    usersuggest_profile = []
    usersuggest_profile_list = []

    for user in new_suggestions_list:
        usersuggest_profile.append(user.id)
    for ids in usersuggest_profile:
        profile_lists = Profile.objects.filter(userid=ids)
        for profile_list in profile_lists:
            profile_list.followers = FollowersCount.objects.filter(
                user=profile_list.user).count()
        usersuggest_profile_list.append(profile_lists)

    usersuggest_profile_list = list(chain(*usersuggest_profile_list))
    # print(usersuggest_profile_list)

    return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed, 'usersuggest_profile_list': usersuggest_profile_list[:4]})


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already exists')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already exists')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username,
                                                email=email, password=password)
                user.save()
                messages.info(request, 'User created')

                # log in and redirect to setting page
                user_login = auth.authenticate(
                    username=username, password=password)
                auth.login(request, user_login)

                # create a Profile object for the user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(
                    user=user_model, userid=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.error(request, 'Password does not match')
            return redirect('signup')
    else:
        return render(request, 'signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('signin')
    else:
        return render(request, 'signin.html')


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def settings(request):
    main_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = main_profile.profile_pic
            bio = request.POST.get('bio')
            location = request.POST.get('location')

            main_profile.bio = bio
            main_profile.location = location
            main_profile.save()
        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST.get('bio')
            location = request.POST.get('location')

            main_profile.bio = bio
            main_profile.location = location
            main_profile.profile_pic = image
            main_profile.save()

        return redirect('settings')

    return render(request, 'settings.html', {'main_profile': main_profile})


@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        music = request.FILES.get('music_upload')
        caption = request.POST.get('caption')
        post = Post.objects.create(
            user=user, image=image, music=music, caption=caption)
        post.save()
        return redirect('/')
    else:
        return redirect('/')


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(
        post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes += 1
        post.save()
        return HttpResponse(post.no_of_likes)
    else:
        post.no_of_likes -= 1
        post.save()
        like_filter.delete()
        return HttpResponse(post.no_of_likes)


@login_required(login_url='signin')
def profile(request, pk):
    main_object = User.objects.get(username=request.user.username)
    main_profile = Profile.objects.get(user=main_object)

    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_posts_length = len(user_posts)

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        follow = 'UnFollow'
    else:
        follow = 'Follow'

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        'main_profile': main_profile,
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_posts_length': user_posts_length,
        'follow': follow,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST.get('follower')
        user = request.POST.get('user')

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follow = FollowersCount.objects.get(
                follower=follower, user=user)
            delete_follow.delete()
            return redirect('/profile/' + user)
        else:
            new_follow = FollowersCount.objects.create(
                follower=follower, user=user)
            new_follow.save()
            return redirect('/profile/' + user)
    else:
        return redirect('/')


@login_required(login_url='signin')
def search(request):

    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST.get('username')
        user_object = User.objects.filter(username__icontains=username)

        username_profile = []
        user_profile_list = []

        for user in user_object:
            username_profile.append(user.id)

        for ids in username_profile:
            profile_list = Profile.objects.filter(userid=ids)
            user_profile_list.append(profile_list)

        user_profile_list = list(chain(*user_profile_list))
        print(user_profile_list)
    return render(request, 'search.html', {'user_profile': user_profile, 'user_profile_list': user_profile_list})


@login_required(login_url='signin')
def delete_event(request, pk):
    post = Post.objects.get(id=pk)
    post.delete()
    return redirect('/')


@login_required(login_url='signin')
def view_post(request, pk):
    user_object = User.objects.get(username=request.user.username)
    main_profile = Profile.objects.get(user=user_object)

    post = Post.objects.get(id=pk)

    if request.method == 'POST':
        comment = request.POST.get('comment')
        comment_post = Comment.objects.create(
            user=request.user.username, post=post, comment=comment)
        comment_post.save()
        return redirect('/post/' + str(pk))
    user_object = User.objects.get(username=post.user)
    user_profile = Profile.objects.get(user=user_object)
    return render(request, 'view_post.html', {'main_profile': main_profile,
                                              'post': post,
                                              'user_profile': user_profile})


@login_required(login_url='signin')
def messages_view(request):
    threads = Thread.objects.by_user(user=request.user).order_by('-updated_at')
    user_object = User.objects.get(username=request.user.username)
    main_profile = Profile.objects.get(user=user_object)
    context = {
        'Threads': threads,
        'main_profile': main_profile,
    }
    return render(request, 'message.html', context)


@login_required(login_url='signin')
def get_messages(request):
    pk = request.GET.get('thread_id')
    thread = Thread.objects.get(id=pk)
    receiver = thread.second_person if request.user == thread.first_person else thread.first_person
    context = {
        'thread': thread,
        'receiver': receiver,
    }
    return render(request, 'messages.html', context)


@login_required(login_url='signin')
def sendmessage(request, pk):
    thread, is_created = Thread.objects.get_or_create(
        user=request.user, receiver=User.objects.get(pk=pk))
    thread.save(update_fields=['updated_at'])
    return redirect('/messages/')
