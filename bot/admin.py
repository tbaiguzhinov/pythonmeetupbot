from django.contrib import admin
from .models import User, Meetup, Stream, Report, Donation, Question

<<<<<<< HEAD
from django.contrib import admin

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = [
        'telegram_id',
    ]
=======
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from bot.models import User, Meetup, Stream, Report, Block

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


class ReportInline(NestedStackedInline):
    model = Report
    extra = 1


class BlockInline(NestedStackedInline):
    model = Block
    extra = 1
    inlines = [
        ReportInline,
    ]


class StreamInline(NestedStackedInline):
    model = Stream
    extra = 1
    inlines = [
        BlockInline,
    ]


@admin.register(Meetup)
class MeetupAdmin(NestedModelAdmin):
    model = Meetup
    fields = ('title', 'date')
    inlines = [
        StreamInline,
        ]
>>>>>>> 2e6372afef38d17ccb4fa45f988d168d2870ca8a
