from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.diary_create, name='diary_create'),
    path('edit/<int:pk>/', views.diary_edit, name='diary_edit'),
    path('d/<uuid:sharing_link>/', views.diary_detail, name='diary_detail'),
    path('logout/', LogoutView.as_view(template_name='diary/logout.html'), name='logout'),
    path('calendar/event/create/', views.calendar_event_create, name='calendar_event_create'),
    path('calendar/event/<int:pk>/edit/', views.calendar_event_edit, name='calendar_event_edit'),
    path('calendar/event/<int:pk>/delete/', views.calendar_event_delete, name='calendar_event_delete'),
    path('calendar/event/<int:pk>/move/', views.calendar_event_move, name='calendar_event_move'),
    path('public/', views.public_calendar, name='public_calendar'),
    path('public/<str:username>/', views.public_calendar, name='public_calendar_user'),
    path('public/event/<int:event_id>/comment/', views.add_comment, name='add_comment'),
    path('public/event/<int:event_id>/upvote/', views.upvote_event, name='upvote_event'),
    path('public/event/<int:event_id>/remind/', views.set_reminder, name='set_reminder'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('feed/', views.feed, name='feed'),
    path('messages/inbox/', views.inbox, name='inbox'),
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/compose/<str:username>/', views.compose_message, name='compose_message_to'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('notifications/', views.notifications, name='notifications'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    path('notifications/settings/', views.notification_settings, name='notification_settings'),
] 