from django.db import models
from django.contrib.auth.models import User
import uuid

class DiaryEntry(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='diary_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sharing_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    collaborators = models.ManyToManyField(User, related_name='collaborative_diaries', blank=True)

    def __str__(self):
        return self.title

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    image = models.ImageField(upload_to='diary_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=True, help_text='Show this event on your public calendar?')
    categories = models.ManyToManyField('Category', blank=True, related_name='events')

    def __str__(self):
        return f"{self.title} ({self.date})"

class Comment(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.name} on {self.event.title}"

class Upvote(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='upvotes')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'ip_address')

    def __str__(self):
        return f"Upvote for {self.event.title} from {self.ip_address}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    notify_upvote = models.BooleanField(default=True)
    notify_comment = models.BooleanField(default=True)
    notify_follow = models.BooleanField(default=True)
    notify_message = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username} at {self.sent_at}"

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    def __str__(self):
        return self.name

class Notification(models.Model):
    NOTIF_TYPES = [
        ('upvote', 'Upvote'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES)
    text = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.text}"
