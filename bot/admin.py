from django.contrib import admin
from .models import User, Meetup, Stream, Report, Donation, Question

from django.contrib import admin

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = [
        'telegram_id',
    ]