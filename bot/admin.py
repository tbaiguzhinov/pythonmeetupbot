from django.contrib import admin
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import re_path, reverse
from django.utils.html import format_html
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from bot.form import SendUserNotification
from bot.models import Block, Donation, Meetup, Report, Stream, User


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
    fields = ('title', 'date', 'status')
    list_display = (
        'title',
        'id',
        'status',
        'send_notification'
    )
    inlines = [
        StreamInline,
        ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
                    re_path(
                        '(?P<meetup_id>.+)/message/',
                        self.admin_site.admin_view(self.send_message),
                        name='meetup-message'
                    ),
        ]
        return custom_urls + urls

    def send_notification(self, obj):
        return format_html(
            '<a class="button" href="{}">Оповестить</a>&nbsp;',
            reverse('admin:meetup-message', args=[obj.pk]),
        )
    send_notification.short_description = 'Оповестить пользователей'
    send_notification.allow_tags = True

    def send_message(self, request, meetup_id, *args, **kwargs):
        return self.process_action(
            request=request,
            meetup_id=meetup_id,
            action_form=SendUserNotification,
            action_title='Notification',
        )

    def process_action(
        self,
        request,
        meetup_id,
        action_form,
        action_title
    ):
        meetup = self.get_object(request, meetup_id)
        if request.method != 'POST':
            form = action_form()
        else:
            form = action_form(request.POST)
            if form.is_valid():
                try:
                    form.form_action(request.POST['message'], meetup_id)
                except ValidationError as e:
                    self.message_user(request, 'Ошибка, введите корректное сообщение')
                    pass
                self.message_user(request, 'Сообщение отправлено')
                url = reverse(
                    'admin:index',
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['meetup'] = meetup
        context['title'] = action_title

        return TemplateResponse(
            request,
            'bot_meetup.html',
            context,
        )


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'donated_by',
        'sum',
        'donated_at'
    )
