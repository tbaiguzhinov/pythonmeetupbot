import os

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from bot.models import User

def start(update: Update, context: CallbackContext):

    user = User.objects.filter(telegram_token=update.effective_user.id).get()

    if user:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello, {user.first_name}!")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, user!")


class Command(BaseCommand):

    def handle(self, *args, **options):
        load_dotenv()

        updater = Updater(token=os.getenv("TELEGRAM_API_KEY"), use_context=True)
        dispatcher = updater.dispatcher

        start_handler = CommandHandler('start', start)
        dispatcher.add_handler(start_handler)
        
        updater.start_polling()
        updater.idle()
