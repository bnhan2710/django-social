from django.urls import path
from . import views
from . import debug_views

urlpatterns = [
    path('', views.index, name='index'),
    path('settings/', views.settings, name='settings'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('ws-debug/', debug_views.websocket_debug, name='websocket_debug'),
    path('logout', views.logout, name='logout'),
    path('upload', views.upload, name='upload'),
    path('like-post', views.like_post, name='like-post'),
    path('profile/<str:pk>', views.profile, name='profile'),
    path('post/<str:pk>', views.view_post, name='view_post'),
    path('follow', views.follow, name='follow'),
    path('search', views.search, name='search'),
    path('messages/', views.messages_view, name='messages_view'),
    path('sendmessage/<str:pk>', views.sendmessage, name='sendmessage'),
    path('messages/getmessages', views.get_messages, name='get_messages'),
    path('api/messages/<int:thread_id>/', views.api_get_messages, name='api_get_messages'),
    path('api/messages/unread/', views.get_unread_counts, name='get_unread_counts'),
    path('messages/create-group/', views.create_group_chat, name='create_group_chat'),
    path('test-websocket/', views.test_websocket, name='test_websocket'),
    path('delete/<str:pk>', views.delete_event, name='delete_event'),
    path('edit-post/<uuid:pk>/', views.edit_post, name='edit_post'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('popular/', views.popular_posts, name='popular_posts'),
    path('friends-network/', views.friends_network, name='friends_network'),
    path('followers/<str:username>/', views.followers_list, name='followers_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
]
