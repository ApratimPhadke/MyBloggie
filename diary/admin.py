from .models import DiaryEntry
from django.contrib import admin

# Register your models here.
admin.site.register(DiaryEntry)

admin.site.site_header = 'Administration'
admin.site.site_title = 'Administration'
admin.site.index_title = 'Administration'
