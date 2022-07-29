import os

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.tg_bot import (
    HANDLE_FORM,
    select_speaker_menu,
    program_handle_menu,
    start,
    flow_handle_menu,
    flow_question_timeline,
    handle_error,
    end_conversation,
    form_handle,
    ask_form_questions,
    send_message_to_speaker,
    START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_QUESTION, HANDLE_FLOW, CLOSE, SEND_QUESTION
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as exc:
            raise


def start_bot():
    token = settings.TOKEN_TELEGRAM
    """add a loggining a bit later"""
    #user_id = settings.TG_USER_ID
    #logging_token = settings.TG_TOKEN_LOGGING
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
                CallbackQueryHandler(flow_handle_menu, pattern="^(questions)$"),
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)$"),
                CallbackQueryHandler(form_handle, pattern="^(form)$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
                ],
            HANDLE_FORM: [
                MessageHandler(Filters.text & ~Filters.command, ask_form_questions),
            ],
            HANDLE_FLOW: [
                CallbackQueryHandler(start, pattern="^(back)$"),
                CallbackQueryHandler(flow_handle_menu, pattern="^(flow)\d*$"),
                CallbackQueryHandler(flow_question_timeline, pattern="^(timeline)$")
            ],
            HANDLE_PROGRAMS: [
                CallbackQueryHandler(program_handle_menu, pattern="^(programs)\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            HANDLE_QUESTION: [
                CallbackQueryHandler(select_speaker_menu, pattern="^(flow|)\d*$"),
                CallbackQueryHandler(select_speaker_menu, pattern="^(speaker|)\d*$"),
                CallbackQueryHandler(start, pattern="^(back)$"),
            ],
            SEND_QUESTION: [
                MessageHandler(Filters.text & ~Filters.command, send_message_to_speaker)
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
