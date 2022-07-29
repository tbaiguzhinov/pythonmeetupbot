from django.contrib import admin
from .models import User, Meetup, Stream, Report, Donation, Question

from django.contrib import admin

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
