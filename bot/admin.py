from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from bot.models import Block, Meetup, Report, Stream, User

from .form import SendUserNotification
from .models import Donation, Meetup, Question, Report, Stream, User
from django.urls import path, re_path
from django.template.response import TemplateResponse

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
    #change_form_template = "bot/templates/admin/bot/bot_meetup.html"
    #'bot/meetup/[0-9]+/message/'
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
            print('if')

        else:
            print('else')
            form = action_form(request.POST)
            print(request.POST['message'])
            if form.is_valid():
                try:
                    print(form.form_action('sdsds'))
                    form.form_action('sdsds')
                except Exception as e:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass
            else:
                self.message_user(request, 'Success')
                url = reverse(
                    'admin::bot_meetup',
                    args=[meetup.pk],
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
        