from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import DiaryEntry, CalendarEvent, Comment, Upvote, UserProfile, Follow, Message, Category, Notification
from .forms import DiaryEntryForm, CalendarEventForm, UserProfileForm, MessageForm
from django.contrib.auth.models import User
import os
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
import random
from django.http import JsonResponse
import json
from datetime import datetime
from django.views.decorators.http import require_POST
import time
from django.utils import timezone
from django.contrib import messages
import random as pyrandom
from django.core.mail import send_mail

THOUGHTS = [
    "Every day is a new page in your story.",
    "Happiness is found in the little things.",
    "Write your heart out, the world is listening.",
    "A diary is a friend who listens without judgment.",
    "Let your words be your wings.",
    "Memories are timeless treasures of the heart.",
    "Your story matters."
]

def home(request):
    if request.user.is_authenticated:
        entries = (DiaryEntry.objects.filter(owner=request.user) | DiaryEntry.objects.filter(collaborators=request.user)).distinct()
        entry_count = entries.count()
        collaborator_count = set()
        for entry in entries:
            collaborator_count.update(entry.collaborators.all())
        collaborator_count = len(collaborator_count)
        calendar_events = CalendarEvent.objects.filter(user=request.user)
        unread_notifications_count = request.user.notifications.filter(read=False).count()
    else:
        entries = DiaryEntry.objects.none()
        entry_count = 0
        collaborator_count = 0
        calendar_events = CalendarEvent.objects.none()
        unread_notifications_count = 0
    thought = random.choice(THOUGHTS)
    return render(request, 'diary/home.html', {
        'entries': entries,
        'thought': thought,
        'entry_count': entry_count,
        'collaborator_count': collaborator_count,
        'calendar_events': calendar_events,
        'unread_notifications_count': unread_notifications_count,
    })

@login_required
def diary_create(request):
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST, request.FILES)
        if form.is_valid():
            diary = form.save(commit=False)
            diary.owner = request.user
            diary.save()
            form.save_m2m()
            return redirect('home')
    else:
        form = DiaryEntryForm()
    return render(request, 'diary/diary_form.html', {'form': form})

@login_required
def diary_edit(request, pk):
    diary = get_object_or_404(DiaryEntry, pk=pk)
    if request.user != diary.owner and request.user not in diary.collaborators.all():
        return redirect('home')
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST, request.FILES, instance=diary)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DiaryEntryForm(instance=diary)
    return render(request, 'diary/diary_form.html', {'form': form, 'edit': True})

def diary_detail(request, sharing_link):
    diary = get_object_or_404(DiaryEntry, sharing_link=sharing_link)
    can_edit = request.user == diary.owner or request.user in diary.collaborators.all()
    return render(request, 'diary/diary_detail.html', {'diary': diary, 'can_edit': can_edit})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'diary/signup.html', {'form': form})

@login_required
def calendar_event_create(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            form.save_m2m()
            # Handle new categories
            new_cats = form.cleaned_data.get('new_categories', '')
            if new_cats:
                from django.utils.text import slugify
                for name in [n.strip() for n in new_cats.split(',') if n.strip()]:
                    cat, created = Category.objects.get_or_create(slug=slugify(name), defaults={'name': name})
                    event.categories.add(cat)
            return redirect('home')
    else:
        form = CalendarEventForm()
    return render(request, 'diary/calendar_event_form.html', {'form': form})

@login_required
def calendar_event_edit(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            # Handle new categories
            new_cats = form.cleaned_data.get('new_categories', '')
            if new_cats:
                from django.utils.text import slugify
                for name in [n.strip() for n in new_cats.split(',') if n.strip()]:
                    cat, created = Category.objects.get_or_create(slug=slugify(name), defaults={'name': name})
                    event.categories.add(cat)
            return redirect('home')
    else:
        form = CalendarEventForm(instance=event)
    return render(request, 'diary/calendar_event_form.html', {'form': form, 'edit': True})

@login_required
def calendar_event_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk, user=request.user)
    if request.method == 'POST':
        event.delete()
        return redirect('home')
    return render(request, 'diary/calendar_event_confirm_delete.html', {'event': event})

@login_required
def calendar_event_move(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(CalendarEvent, pk=pk, user=request.user)
        data = json.loads(request.body)
        new_date = data.get('date')
        if new_date:
            try:
                event.date = datetime.fromisoformat(new_date).date()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)
            event.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'No date provided'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def public_calendar(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = User.objects.first()
    events = CalendarEvent.objects.filter(user=user, public=True)
    categories = Category.objects.all()
    selected_category = request.GET.get('category')
    if selected_category:
        events = events.filter(categories__slug=selected_category)
    # Generate a simple math captcha for the comment form
    a, b = pyrandom.randint(1, 9), pyrandom.randint(1, 9)
    request.session['captcha_answer'] = a + b
    return render(request, 'diary/public_calendar.html', {
        'events': events,
        'calendar_user': user,
        'categories': categories,
        'captcha_question': f"{a} + {b} = ?",
    })

RATE_LIMIT = 3  # max actions per hour per IP per event
RATE_LIMIT_WINDOW = 3600  # seconds

def is_rate_limited(ip, event_id, action):
    key = f"rate_{action}_{event_id}_{ip}"
    now = int(time.time())
    window_start = now - RATE_LIMIT_WINDOW
    history = request.session.get(key, [])
    # Remove timestamps outside the window
    history = [t for t in history if t > window_start]
    if len(history) >= RATE_LIMIT:
        return True
    history.append(now)
    request.session[key] = history
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_notification(user, notif_type, text, url=None):
    profile = getattr(user, 'profile', None)
    if not profile:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
    if notif_type == 'upvote' and not profile.notify_upvote:
        return
    if notif_type == 'comment' and not profile.notify_comment:
        return
    if notif_type == 'follow' and not profile.notify_follow:
        return
    if notif_type == 'message' and not profile.notify_message:
        return
    Notification.objects.create(user=user, notif_type=notif_type, text=text, url=url or '')

@require_POST
def add_comment(request, event_id):
    event = get_object_or_404(CalendarEvent, pk=event_id, public=True)
    name = request.POST.get('name', 'Anonymous')
    text = request.POST.get('text', '')
    captcha = request.POST.get('captcha', '')
    ip = get_client_ip(request)
    if is_rate_limited(ip, event_id, 'comment'):
        messages.error(request, 'Too many comments from your IP. Please try again later.')
        return redirect('public_calendar')
    try:
        if int(captcha) != request.session.get('captcha_answer'):
            messages.error(request, 'CAPTCHA answer is incorrect.')
            return redirect('public_calendar')
    except Exception:
        messages.error(request, 'CAPTCHA answer is required.')
        return redirect('public_calendar')
    if text:
        Comment.objects.create(event=event, name=name, text=text)
        # Notify event owner
        if event.user:
            create_notification(
                user=event.user,
                notif_type='comment',
                text=f'New comment on your event "{event.title}"',
                url=f'/public/'
            )
    return redirect('public_calendar')

@require_POST
def upvote_event(request, event_id):
    event = get_object_or_404(CalendarEvent, pk=event_id, public=True)
    ip = get_client_ip(request)
    if is_rate_limited(ip, event_id, 'upvote'):
        messages.error(request, 'Too many upvotes from your IP. Please try again later.')
        return redirect('public_calendar')
    if not Upvote.objects.filter(event=event, ip_address=ip).exists():
        Upvote.objects.create(event=event, ip_address=ip)
        # Notify event owner
        if event.user:
            create_notification(
                user=event.user,
                notif_type='upvote',
                text=f'Your event "{event.title}" got a new upvote!',
                url=f'/public/'
            )
    return redirect('public_calendar')

@require_POST
def set_reminder(request, event_id):
    event = get_object_or_404(CalendarEvent, pk=event_id, public=True)
    email = request.POST.get('reminder_email', '').strip()
    if not email:
        messages.error(request, 'Email is required for reminders.')
        return redirect('public_calendar')
    # Prevent duplicate reminders in session
    reminders = request.session.get('reminders', set())
    if not isinstance(reminders, list):
        reminders = list(reminders)
    key = f'{event_id}:{email}'
    if key in reminders:
        messages.info(request, 'You have already set a reminder for this event.')
        return redirect('public_calendar')
    reminders.append(key)
    request.session['reminders'] = reminders
    # Send email (or just show a message if not configured)
    try:
        send_mail(
            subject=f'Reminder set for {event.title}',
            message=f'This is a reminder for the event "{event.title}" on {event.date}.',
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
        messages.success(request, 'Reminder set! You will receive an email.')
    except Exception:
        messages.success(request, 'Reminder set! (Email not sent in demo mode)')
    return redirect('public_calendar')

def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = getattr(user, 'profile', None)
    public_events = CalendarEvent.objects.filter(user=user, public=True)
    upvote_count = sum(event.upvotes.count() for event in public_events)
    return render(request, 'diary/profile.html', {
        'profile_user': user,
        'profile': profile,
        'public_events': public_events,
        'upvote_count': upvote_count,
    })

@login_required
def profile_edit(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'diary/profile_edit.html', {'form': form})

@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user and not Follow.objects.filter(follower=request.user, following=target).exists():
        Follow.objects.create(follower=request.user, following=target)
        messages.success(request, f'You are now following {target.username}.')
        # Notify followed user
        create_notification(
            user=target,
            notif_type='follow',
            text=f'{request.user.username} started following you.',
            url=f'/profile/{request.user.username}/'
        )
    return redirect('profile', username=target.username)

@login_required
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, following=target).delete()
    messages.success(request, f'You have unfollowed {target.username}.')
    return redirect('profile', username=target.username)

@login_required
def feed(request):
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    events = CalendarEvent.objects.filter(user__in=following_users, public=True).order_by('-date')[:30]
    return render(request, 'diary/feed.html', {'events': events})

@login_required
def inbox(request):
    messages_in = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    return render(request, 'diary/inbox.html', {'messages_in': messages_in})

@login_required
def sent_messages(request):
    messages_out = Message.objects.filter(sender=request.user).order_by('-sent_at')
    return render(request, 'diary/sent_messages.html', {'messages_out': messages_out})

@login_required
def message_detail(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if msg.recipient == request.user:
        msg.read = True
        msg.save()
    if msg.recipient != request.user and msg.sender != request.user:
        return redirect('inbox')
    return render(request, 'diary/message_detail.html', {'msg': msg})

@login_required
def compose_message(request, username=None):
    recipient = None
    if username:
        recipient = get_object_or_404(User, username=username)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid() and recipient:
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = recipient
            msg.save()
            messages.success(request, f'Message sent to {recipient.username}!')
            # Notify recipient
            create_notification(
                user=recipient,
                notif_type='message',
                text=f'New message from {request.user.username}',
                url=f'/messages/{msg.pk}/'
            )
            return redirect('inbox')
    else:
        form = MessageForm()
    return render(request, 'diary/compose_message.html', {'form': form, 'recipient': recipient})

@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read
    notifs.update(read=True)
    return render(request, 'diary/notifications.html', {'notifications': notifs})

@login_required
def notification_count_api(request):
    count = request.user.notifications.filter(read=False).count()
    return JsonResponse({'unread_count': count})

@login_required
def notification_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification settings updated!')
            return redirect('notification_settings')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'diary/notification_settings.html', {'form': form})
