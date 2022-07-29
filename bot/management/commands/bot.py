import os
import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.tg_bot import (
    HANDLE_FORM,
    question_handle_menu,
    program_handle_menu,
    start,
    stream_handle_menu,
    handle_block_reports,
    handle_error,
    end_conversation,
    form_handle,
    ask_form_questions,
    START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_QUESTIONS, HANDLE_FLOW,\
    HANDLE_BLOCK, CLOSE
)
from bot.logging_handler import TelegramLogsHandler

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as exc:
            raise


def start_bot():
    token = settings.TOKEN_TELEGRAM
    """add a loggining a bit later"""
    user_id = settings.TG_USER_ID
    logging_token = settings.TG_TOKEN_LOGGING
    logging_token = os.getenv('TG_TOKEN_LOGGING')
    logging_bot = Bot(token=logging_token)
    logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(tg_bot=logging_bot, chat_id=user_id))
    logger.info('PythonMeetup bot запущен')
    """Start the bot."""
    updater = Updater(token)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                MessageHandler(Filters.text, start),
                ],
            HANDLE_MENU: [
                CallbackQueryHandler(question_handle_menu, pattern="^(questions)$"),
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)$"),
                CallbackQueryHandler(form_handle, pattern="^(form)$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
                ],
            HANDLE_FORM: [
                MessageHandler(Filters.text & ~Filters.command, ask_form_questions),
            ],
            HANDLE_FLOW: [
                CallbackQueryHandler(start, pattern="^(back)$"),
                CallbackQueryHandler(stream_handle_menu, pattern="^(reports)\S\d*$"),
            ],
            HANDLE_PROGRAMS: [
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            HANDLE_QUESTIONS: [
                CallbackQueryHandler(question_handle_menu, pattern="^(questions)\S\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            HANDLE_BLOCK: [
                CallbackQueryHandler(handle_block_reports, pattern="^(blockreport)\S\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            CLOSE: [
                
            ]
        },
        fallbacks=[CommandHandler("end", end_conversation)],
        name="my_conversation",
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()
    updater.idle()
