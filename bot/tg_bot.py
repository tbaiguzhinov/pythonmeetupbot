
import os
#import time
#from functools import partial

from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.static_text import greetings_message


START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_QUESTIONS, HANDLE_FLOW, CLOSE = range(6)


def create_greetings_menu():
    keyboard = []
    programs_button = [InlineKeyboardButton('Программа', callback_data='programs')]
    keyboard.append(programs_button)
    questions_keyboard = [InlineKeyboardButton('Вопросы спикерам', callback_data='questions')]
    keyboard.append(questions_keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def create_menu(products):
    keyboard = []
    callbackdata, items = products
    for product in items:
        product_button = [InlineKeyboardButton(product.name, callback_data=f'{callbackdata}{product.id}')]
        keyboard.append(product_button) 
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup    


def start(update: Update, context: CallbackContext) -> None:
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    context.bot.send_message(
        chat_id=chat_id,
        text=greetings_message,
        reply_markup=create_greetings_menu()
        )
    return HANDLE_MENU


def flow_handle_menu(update: Update, context: CallbackContext) -> None:
    #flows = Flow.objects.all()
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    query = update.callback_query
    if query == 'programs':
        #flows = Program.objects.flows
        flows = ('flow', [])
        context.bot.send_message(
        chat_id=chat_id,
        text='Пожалуйста выберите поток',
        reply_markup=create_menu(flows)
        )
        return HANDLE_PROGRAMS
    elif query == 'questions':
        #flows = Question.objects.flows
        flows = ('flow', [])
        context.bot.send_message(
        chat_id=chat_id,
        text='Пожалуйста выберите поток',
        reply_markup=create_menu(flows)
        )
        return HANDLE_FLOW


def flow_question_timeline(update: Update, context: CallbackContext):
    pass


def program_handle_menu(update: Update, context: CallbackContext) -> None:
    #programs = Programms.objects.all()
    programs = ('program', [])
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    context.bot.send_message(
        chat_id=chat_id,
        text='Пожалуйста выберите программу',
        reply_markup=create_menu(programs)
        )
    return HANDLE_PROGRAMS


def question_handle_menu(update: Update, context: CallbackContext) -> None:
    #speakers = Speaker.objects.all()
    speakers = ('speaker', [])
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    context.bot.send_message(
        chat_id=chat_id,
        text='Пожалуйста выберите спикера, которому вы хотите задать вопрос',
        reply_markup=create_menu(speakers)
        )
    return HANDLE_QUESTIONS


def handle_error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""


def end_conversation(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Пока!'
        )
    return ConversationHandler.END
