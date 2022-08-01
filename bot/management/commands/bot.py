import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot
from telegram.ext import (CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.tg_bot import (
    HANDLE_FORM,
    program_handle_menu,
    start,
    stream_handle_menu,
    handle_block_reports,
    handle_error,
    end_conversation,
    form_handle,
    meeting_handle,
    ask_form_questions,
    question_stream_handle_menu,
    select_speaker_menu,
    save_chosen_speaker,
    send_message_to_speaker,
    START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_QUESTION, HANDLE_STREAM,\
    HANDLE_BLOCK, SEND_QUESTION, CLOSE
)
from bot.logging_handler import TelegramLogsHandler
from bot.storing_data import MeetupBotPersistence
import redis

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as exc:
            raise


def start_bot():
    token = settings.TOKEN_TELEGRAM
    redis_host = settings.REDIS_HOST
    redis_port = settings.REDIS_PORT
    redis_pass = settings.REDIS_PASS
    redis_base = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass
        )
    persistence = MeetupBotPersistence(redis_base)
    """add a loggining a bit later"""
    user_id = settings.TG_USER_ID
    logging_token = settings.TG_TOKEN_LOGGING
    logging_bot = Bot(token=logging_token)
    logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    logger.setLevel(logging.DEBUG)
    logger.addHandler(TelegramLogsHandler(tg_bot=logging_bot, chat_id=user_id))
    logger.info('PythonMeetup bot запущен')
    """Start the bot."""
    updater = Updater(token, persistence=persistence)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                MessageHandler(Filters.text, start),
                ],
            HANDLE_MENU: [
                CallbackQueryHandler(question_stream_handle_menu, pattern="^(questions)$"),
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)$"),
                CallbackQueryHandler(form_handle, pattern="^(form)$"),
                CallbackQueryHandler(meeting_handle, pattern="^(meeting)$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
                ],
            HANDLE_FORM: [
                MessageHandler(Filters.text & ~Filters.command, ask_form_questions),
            ],
            HANDLE_STREAM: [
                CallbackQueryHandler(start, pattern="^(back)$"),
                CallbackQueryHandler(stream_handle_menu, pattern="^(reports)\S\d*$"),
            ],
            HANDLE_PROGRAMS: [
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            HANDLE_QUESTION: [
                CallbackQueryHandler(select_speaker_menu, pattern="^(stream_)\d*$"),
                CallbackQueryHandler(save_chosen_speaker, pattern="^(speaker_)\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            SEND_QUESTION: [
                MessageHandler(Filters.text & ~Filters.command, send_message_to_speaker),
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
        persistent=True,
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()
    updater.idle()
