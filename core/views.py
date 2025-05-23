from asyncio import threads
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
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

    # Get posts that the current user has liked
    user_likes = LikePost.objects.filter(username=request.user.username).values_list('post_id', flat=True)
    liked_posts = list(user_likes)
    
    # Get most liked posts - excluding user's own posts and already followed users' posts
    most_liked_posts = Post.objects.exclude(user=request.user.username).exclude(
        user__in=[user for user in user_following_list if isinstance(user, str)]
    ).order_by('-no_of_likes')[:5]
    
    # Process most liked posts to add profile pic
    for post in most_liked_posts:
        user_obj = User.objects.get(username=post.user)
        post.img = Profile.objects.get(user=user_obj).profile_pic.url
        post.post_comments = Comment.objects.filter(post=post).order_by('-created_at')[0:1]
        post.count_comments = Comment.objects.filter(post=post).count()
    
    # Get friends of friends posts
    friends_of_friends_posts = []
    # Get users followed by users that the current user follows
    for followed_user in user_following:
        fof_following = FollowersCount.objects.filter(follower=followed_user.user)
        for fof in fof_following:
            # Skip if it's the current user or someone they already follow
            if fof.user == request.user.username or fof.user in [u.user for u in user_following]:
                continue
                
            # Get posts from this friend of friend
            fof_posts = Post.objects.filter(user=fof.user).order_by('-created_at')
            
            for post in fof_posts:
                user_obj = User.objects.get(username=post.user)
                post.img = Profile.objects.get(user=user_obj).profile_pic.url
                post.post_comments = Comment.objects.filter(post=post).order_by('-created_at')[0:1]
                post.count_comments = Comment.objects.filter(post=post).count()
                post.fof_connection = followed_user.user  # Track who connects them
                friends_of_friends_posts.append(post)
    
    # Take most recent 5 posts
    friends_of_friends_posts = friends_of_friends_posts[:5]
    
    context = {
        'user_profile': user_profile,
        'posts': feed,
        'usersuggest_profile_list': usersuggest_profile_list[:4],
        'liked_posts': liked_posts,
        'most_liked_posts': most_liked_posts,
        'friends_of_friends_posts': friends_of_friends_posts
    }
    
    return render(request, 'index.html', context)


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

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes + 1
        post.save()
        status = 'liked'
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes - 1
        post.save()
        status = 'unliked'

    return JsonResponse({'likes': post.no_of_likes, 'status': status})


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

    # Get posts that the current user has liked
    user_likes = LikePost.objects.filter(username=request.user.username).values_list('post_id', flat=True)
    liked_posts = list(user_likes)
    
    context = {
        'main_profile': main_profile,
        'post': post,
        'user_profile': user_profile,
        'liked_posts': liked_posts
    }
    
    return render(request, 'view_post.html', context)


@login_required(login_url='signin')
def messages_view(request):
    threads = Thread.objects.by_user(user=request.user).order_by('-updated_at')
    user_object = User.objects.get(username=request.user.username)
    main_profile = Profile.objects.get(user=user_object)
    
    # Process threads to add additional information
    for thread in threads:
        # Get the other user in the thread
        other_user = thread.first_person if request.user == thread.second_person else thread.second_person
        thread.other_user = other_user
        
        # Get the other user's profile
        try:
            thread.other_profile = Profile.objects.get(user=other_user)
        except Profile.DoesNotExist:
            thread.other_profile = None
        
        # Get unread count for current user
        thread.unread_count = thread.get_unread_count(request.user)
        
        # Get the last message timestamp in a readable format
        if thread.messages.exists():
            last_message = thread.messages.order_by('-timestamp').first()
            thread.last_message_time = last_message.timestamp
        else:
            thread.last_message_time = thread.updated_at
    
    context = {
        'threads': threads,
        'main_profile': main_profile,
    }
    return render(request, 'message.html', context)


@login_required(login_url='signin')
def get_messages(request):
    thread_id = request.GET.get('thread_id')
    
    try:
        thread = Thread.objects.get(id=thread_id)
        
        # Check if user is part of this thread
        if request.user != thread.first_person and request.user != thread.second_person:
            return HttpResponseForbidden("You don't have permission to access this thread")
        
        # Get the other user in the thread
        other_user = thread.first_person if request.user == thread.second_person else thread.second_person
        
        # Mark thread as read
        thread.mark_as_read(request.user)
        
        # Mark all messages from the other user as read
        ChatMessage.objects.filter(thread=thread, user=other_user, is_read=False).update(is_read=True)
        
        context = {
            'thread': thread,
            'other_user': other_user,
        }
        return render(request, 'messages.html', context)
    except Thread.DoesNotExist:
        return HttpResponseNotFound("Thread not found")


@login_required(login_url='signin')
def api_get_messages(request, thread_id):
    from django.http import JsonResponse
    
    try:
        thread = Thread.objects.get(id=thread_id)
        
        # Check if user is part of this thread
        if request.user != thread.first_person and request.user != thread.second_person:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Mark thread as read
        thread.mark_as_read(request.user)
        
        # Get the other user in the thread
        other_user = thread.first_person if request.user == thread.second_person else thread.first_person
        
        # Get other user's profile
        try:
            other_profile = Profile.objects.get(user=other_user)
            profile_pic_url = other_profile.profile_pic.url
        except Profile.DoesNotExist:
            profile_pic_url = None
        
        # Get current user's profile
        try:
            user_profile = Profile.objects.get(user=request.user)
            user_profile_pic_url = user_profile.profile_pic.url
        except Profile.DoesNotExist:
            user_profile_pic_url = None
        
        messages = []
        for chat in thread.messages.all().order_by('timestamp'):
            # Determine profile picture URL based on message sender
            profile_pic = user_profile_pic_url if chat.user == request.user else profile_pic_url
            
            messages.append({
                'id': chat.id,
                'message': chat.message,
                'user_id': chat.user.id,
                'username': chat.user.username,
                'timestamp': chat.get_timestamp(),
                'profile_pic': profile_pic,
                'is_read': chat.is_read
            })
        
        # Mark messages as read
        ChatMessage.objects.filter(thread=thread).exclude(user=request.user).filter(is_read=False).update(is_read=True)
        
        return JsonResponse({
            'thread_id': thread_id,
            'messages': messages,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username,
                'profile_pic': profile_pic_url
            }
        })
    except Thread.DoesNotExist:
        return JsonResponse({'error': 'Thread not found'}, status=404)


@login_required(login_url='signin')
def sendmessage(request, pk):
    try:
        receiver = User.objects.get(pk=pk)
        thread, is_created = Thread.objects.get_or_create(user=request.user, receiver=receiver)
        
        # If POST request with message content
        if request.method == 'POST' and request.POST.get('message'):
            message_content = request.POST.get('message').strip()
            if message_content:
                # Create the message
                message = ChatMessage.objects.create(
                    thread=thread,
                    user=request.user,
                    message=message_content
                )
                
                # Update thread
                thread.last_message = message_content
                thread.save(update_fields=['updated_at', 'last_message'])
                
                # Increment unread count for receiver
                if request.user == thread.first_person:
                    thread.unread_messages_count_second += 1
                else:
                    thread.unread_messages_count_first += 1
                thread.save()
                
                # If AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message_id': message.id,
                        'timestamp': message.get_timestamp()
                    })
        
        # If AJAX request for thread info
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'thread_id': thread.id
            })
            
        return redirect(f'/messages/?thread_id={thread.id}')
    except User.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'User not found'}, status=404)
        return redirect('/messages/')


@login_required(login_url='signin')
def create_group_chat(request):
    if request.method == 'POST':
        # This is a placeholder for future group chat functionality
        pass
    return redirect('/messages/')


@login_required(login_url='signin')
def get_unread_counts(request):
    from django.http import JsonResponse
    
    threads = Thread.objects.by_user(user=request.user)
    unread_counts = {}
    total_unread = 0
    
    for thread in threads:
        unread = thread.get_unread_count(request.user)
        unread_counts[thread.id] = unread
        total_unread += unread
    
    return JsonResponse({
        'unread_counts': unread_counts,
        'total_unread': total_unread
    })


@login_required(login_url='signin')
def edit_post(request, pk):
    post = Post.objects.get(id=pk)
    
    # Check if the current user is the post owner
    if request.user.username != post.user:
        return redirect('/')
    
    if request.method == 'POST':
        caption = request.POST.get('caption')
        
        # Handle the image update if provided
        if request.FILES.get('image_upload'):
            # If there's an existing image, delete it (optional)
            if post.image:
                post.image.delete()
            post.image = request.FILES.get('image_upload')
        
        # Handle the music update if provided
        if request.FILES.get('music_upload'):
            # If there's existing music, delete it (optional)
            if post.music:
                post.music.delete()
            post.music = request.FILES.get('music_upload')
        
        post.caption = caption
        post.save()
        
        return redirect('/post/' + str(pk))
    
    context = {
        'post': post
    }
    return render(request, 'edit_post.html', context)


@login_required(login_url='signin')
def recommendations(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    main_profile = user_profile
    
    # Get users that the current user follows
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    following_usernames = [user.user for user in user_following]
    
    # Dictionary to keep track of friends of friends posts and their connections
    fof_posts_dict = {}
    
    # Get friends of friends posts
    for followed_username in following_usernames:
        # Find who your friends follow (friends of friends)
        fof_following = FollowersCount.objects.filter(follower=followed_username)
        
        for fof in fof_following:
            # Skip if it's the current user or someone they already follow
            if fof.user == request.user.username or fof.user in following_usernames:
                continue
            
            # Get posts from this friend of friend
            fof_posts = Post.objects.filter(user=fof.user).order_by('-created_at')
            
            for post in fof_posts:
                # If we haven't processed this post yet
                if str(post.id) not in fof_posts_dict:
                    user_obj = User.objects.get(username=post.user)
                    post.img = Profile.objects.get(user=user_obj).profile_pic.url
                    post.post_comments = Comment.objects.filter(post=post).order_by('-created_at')[:3]
                    post.count_comments = Comment.objects.filter(post=post).count()
                    
                    # Keep track of all connections that lead to this post
                    post.connections = [followed_username]
                    fof_posts_dict[str(post.id)] = post
                else:
                    # Add another connection path if this is a different friend connecting to the same post
                    if followed_username not in fof_posts_dict[str(post.id)].connections:
                        fof_posts_dict[str(post.id)].connections.append(followed_username)
    
    # Convert dictionary to list
    friends_of_friends_posts = list(fof_posts_dict.values())
    
    # Sort by created_at (most recent first)
    friends_of_friends_posts.sort(key=lambda x: x.created_at, reverse=True)
    
    # Get most liked posts (popular content)
    most_liked_posts = Post.objects.exclude(user=request.user.username).exclude(
        user__in=following_usernames
    ).order_by('-no_of_likes')[:10]
    
    # Process most liked posts to add profile pic and other details
    for post in most_liked_posts:
        user_obj = User.objects.get(username=post.user)
        post.img = Profile.objects.get(user=user_obj).profile_pic.url
        post.post_comments = Comment.objects.filter(post=post).order_by('-created_at')[:3]
        post.count_comments = Comment.objects.filter(post=post).count()
    
    # Get posts that the current user has liked
    user_likes = LikePost.objects.filter(username=request.user.username).values_list('post_id', flat=True)
    liked_posts = list(user_likes)
    
    context = {
        'user_profile': user_profile,
        'main_profile': main_profile,
        'friends_of_friends_posts': friends_of_friends_posts,
        'most_liked_posts': most_liked_posts,
        'liked_posts': liked_posts,
    }
    
    return render(request, 'recommendations.html', context)


@login_required(login_url='signin')
def popular_posts(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    main_profile = user_profile
    
    # Get most liked posts
    most_liked_posts = Post.objects.all().order_by('-no_of_likes')[:20]
    
    # Process most liked posts
    for post in most_liked_posts:
        user_obj = User.objects.get(username=post.user)
        post.img = Profile.objects.get(user=user_obj).profile_pic.url
        post.post_comments = Comment.objects.filter(post=post).order_by('-created_at')[0:2]
        post.count_comments = Comment.objects.filter(post=post).count()
    
    # Get posts that the current user has liked
    user_likes = LikePost.objects.filter(username=request.user.username).values_list('post_id', flat=True)
    liked_posts = list(user_likes)
    
    context = {
        'user_profile': user_profile,
        'main_profile': main_profile,
        'most_liked_posts': most_liked_posts,
        'liked_posts': liked_posts,
    }
    
    return render(request, 'popular_posts.html', context)


@login_required(login_url='signin')
def friends_network(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    # Get users that the current user follows
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    following_list = [user.user for user in user_following]
    
    # Get profile information for followed users
    followed_profiles = []
    for username in following_list:
        try:
            user_obj = User.objects.get(username=username)
            profile = Profile.objects.get(user=user_obj)
            profile.username = username
            followed_profiles.append(profile)
        except (User.DoesNotExist, Profile.DoesNotExist):
            continue
    
    # Get users who follow the current user
    user_followers = FollowersCount.objects.filter(user=request.user.username)
    followers_list = [user.follower for user in user_followers]
    
    # Get mutual connections (users who the current user follows who also follow the current user)
    mutual_connections = [user for user in following_list if user in followers_list]
    
    # Find friends of friends (second-degree connections)
    # Dictionary to keep track of friends of friends with their connecting friends
    friends_of_friends_dict = {}
    
    for friend_username in following_list:
        # Find who your friend follows (friends of your friend)
        try:
            friend_follows = FollowersCount.objects.filter(follower=friend_username).values_list('user', flat=True)
            
            for ff_username in friend_follows:
                # Skip if it's the current user or someone they already follow
                if ff_username == request.user.username or ff_username in following_list:
                    continue
                
                # Add or update the friend of friend entry
                if ff_username not in friends_of_friends_dict:
                    friends_of_friends_dict[ff_username] = {
                        'connecting_friends': [friend_username],
                        'mutual_friends': []
                    }
                else:
                    if friend_username not in friends_of_friends_dict[ff_username]['connecting_friends']:
                        friends_of_friends_dict[ff_username]['connecting_friends'].append(friend_username)
        except Exception as e:
            print(f"Error processing friend {friend_username}: {str(e)}")
            continue
    
    # Now find mutual friends for each friend of friend
    for ff_username in list(friends_of_friends_dict.keys()):
        try:
            # Get users that this friend of friend follows
            ff_follows = FollowersCount.objects.filter(follower=ff_username).values_list('user', flat=True)
            
            # Find mutual friends (people that both the current user and this friend of friend follow)
            mutual_friends = [username for username in following_list if username in ff_follows]
            
            friends_of_friends_dict[ff_username]['mutual_friends'] = mutual_friends
        except Exception as e:
            print(f"Error finding mutual friends for {ff_username}: {str(e)}")
            # Remove this friend of friend if we can't get their data
            friends_of_friends_dict.pop(ff_username, None)
    
    # Convert dictionary to user suggestion objects
    user_suggestions = []
    for ff_username, data in friends_of_friends_dict.items():
        try:
            user_obj = User.objects.get(username=ff_username)
            profile = Profile.objects.get(user=user_obj)
            
            # Add friends of friend data
            profile.connecting_friends = data['connecting_friends']
            profile.mutual_friends = len(data['mutual_friends'])
            profile.mutual_friends_profiles = []
            
            # Get profile info for mutual friends (limited to 3)
            for mutual in data['mutual_friends'][:3]:
                try:
                    mutual_user = User.objects.get(username=mutual)
                    mutual_profile = Profile.objects.get(user=mutual_user)
                    profile.mutual_friends_profiles.append(mutual_profile)
                except (User.DoesNotExist, Profile.DoesNotExist):
                    continue
            
            # Get profile info for connecting friends (limited to 3)
            profile.connecting_friends_profiles = []
            for connecting in data['connecting_friends'][:3]:
                try:
                    connecting_user = User.objects.get(username=connecting)
                    connecting_profile = Profile.objects.get(user=connecting_user)
                    profile.connecting_friends_profiles.append(connecting_profile)
                except (User.DoesNotExist, Profile.DoesNotExist):
                    continue
            
            user_suggestions.append(profile)
        except (User.DoesNotExist, Profile.DoesNotExist, Exception) as e:
            print(f"Error creating suggestion for {ff_username}: {str(e)}")
            continue
    
    # Sort suggestions: first by number of connecting friends, then by mutual friends
    user_suggestions.sort(key=lambda x: (len(getattr(x, 'connecting_friends', [])), getattr(x, 'mutual_friends', 0)), reverse=True)
    
    # Limit to reasonable number but ensure we have enough data
    suggestion_limit = min(12, max(6, len(user_suggestions)))
    
    context = {
        'user_profile': user_profile,
        'followed_profiles': followed_profiles,
        'mutual_connections': mutual_connections,
        'user_suggestions': user_suggestions[:suggestion_limit],
        'main_profile': user_profile,
    }
    
    return render(request, 'friends_network.html', context)


@login_required(login_url='signin')
@login_required(login_url='signin')
def followers_list(request, username):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    # Get the target user
    target_user = User.objects.get(username=username)
    
    # Get users who follow the target user
    followers_objects = FollowersCount.objects.filter(user=username)
    followers_list = []
    
    for follower in followers_objects:
        try:
            follower_user = User.objects.get(username=follower.follower)
            follower_profile = Profile.objects.get(user=follower_user)
            
            # Check if the logged-in user follows this follower
            is_following = FollowersCount.objects.filter(
                follower=request.user.username, 
                user=follower.follower
            ).exists()
            
            followers_list.append({
                'user': follower_user,
                'profile': follower_profile,
                'is_following': is_following
            })
        except (User.DoesNotExist, Profile.DoesNotExist):
            continue
    
    context = {
        'user_profile': user_profile,
        'target_user': target_user,
        'followers_list': followers_list,
        'page_type': 'followers'
    }
    
    return render(request, 'connections.html', context)


@login_required(login_url='signin')
def following_list(request, username):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    # Get the target user
    target_user = User.objects.get(username=username)
    
    # Get users that the target user follows
    following_objects = FollowersCount.objects.filter(follower=username)
    following_list = []
    
    for following in following_objects:
        try:
            following_user = User.objects.get(username=following.user)
            following_profile = Profile.objects.get(user=following_user)
            
            # Check if the logged-in user follows this user
            is_following = FollowersCount.objects.filter(
                follower=request.user.username, 
                user=following.user
            ).exists()
            
            following_list.append({
                'user': following_user,
                'profile': following_profile,
                'is_following': is_following
            })
        except (User.DoesNotExist, Profile.DoesNotExist):
            continue
    
    context = {
        'user_profile': user_profile,
        'target_user': target_user,
        'following_list': following_list,
        'page_type': 'following'
    }
    
    return render(request, 'connections.html', context)


@login_required(login_url='signin')
def test_websocket(request):
    return render(request, 'test_websocket.html')
