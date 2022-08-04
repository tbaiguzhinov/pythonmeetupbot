from django import forms
from bot.tg_bot import send_notifications_to_user


class SendUserNotification(forms.Form):
    message = forms.CharField(
        required=True,
        widget=forms.Textarea,
        help_text='Введите текст сообщения для рассылки'
    )
    change_form_template = "bot/templates/bot_meetup.html"

    def form_action(self, message, meetup_id):
        send_notifications_to_user(message, meetup_id)
        return message
