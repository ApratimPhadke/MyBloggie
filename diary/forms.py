from django import forms
from .models import DiaryEntry, CalendarEvent, UserProfile, Message, Category
from django.contrib.auth.models import User

class DiaryEntryForm(forms.ModelForm):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    class Meta:
        model = DiaryEntry
        fields = ['title', 'content', 'image', 'collaborators']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class CalendarEventForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'date', 'image', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'notify_upvote', 'notify_comment', 'notify_follow', 'notify_message']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message here...'}),
        } 