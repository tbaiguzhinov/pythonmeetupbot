import os
#import time
#from functools import partial
from django.core.exceptions import FieldError
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.static_text import greetings_message
from bot.models import User
import json
import logging
START, HANDLE_MENU, HANDLE_PROGRAMS,\
HANDLE_FORM, HANDLE_QUESTIONS, HANDLE_FLOW, CLOSE = range(7)

logger = logging.getLogger(__name__)


def create_greetings_menu():
    keyboard = []
    programs_button = [InlineKeyboardButton('Программа', callback_data='programs')]
    keyboard.append(programs_button)
    questions_keyboard = [InlineKeyboardButton('Вопросы спикерам', callback_data='questions')]
    keyboard.append(questions_keyboard)
    form_keyboard = [InlineKeyboardButton('Заполнить анкету', callback_data='form')]
    keyboard.append(form_keyboard)
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
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=greetings_message,
        reply_markup=create_greetings_menu()
        )
    return HANDLE_MENU


def flow_handle_menu(update: Update, context: CallbackContext) -> None:
    #flows = Flow.objects.all()
    clean_message(update, context)
    query = update.callback_query
    if query == 'programs':
        #flows = Program.objects.flows
        flows = ('flow', [])
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Пожалуйста выберите поток',
            reply_markup=create_menu(flows)
        )
        return HANDLE_PROGRAMS
    elif query == 'questions':
        #flows = Question.objects.flows
        flows = ('flow', [])
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Пожалуйста выберите поток',
            reply_markup=create_menu(flows)
        )
        return HANDLE_FLOW


def flow_question_timeline(update: Update, context: CallbackContext):
    pass


def program_handle_menu(update: Update, context: CallbackContext) -> None:
    #programs = Programms.objects.all()
    programs = ('program', [])
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток необходимой программы',
        reply_markup=create_menu(programs)
        )
    return HANDLE_PROGRAMS


def question_handle_menu(update: Update, context: CallbackContext) -> None:
    #speakers = Speaker.objects.all()
    speakers = ('speaker', [])
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток где выступает спикер, которому вы хотите задать вопрос',
        reply_markup=create_menu(speakers)
        )
    return HANDLE_QUESTIONS


def form_handle(update: Update, context: CallbackContext):
    clean_message(update, context)
    user_data = context.user_data
    user_data['poll_questions'] = read_poll_questions()
    user_data['answers'] = []
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=user_data['poll_questions'].pop('name'),
        )
    return HANDLE_FORM


def ask_form_questions(update: Update, context: CallbackContext):
    user_data = context.user_data
    if user_data['poll_questions']:
        for question in user_data['poll_questions']:
            user_data['answers'].extend([update.message.text])
            context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text=user_data['poll_questions'].pop(question),
                )
            return HANDLE_FORM
    else:
        user_data['answers'].extend([update.message.text])
        try:
            name, company, position, email, telegram = user_data['answers']
            try:
                first_name, last_name = name.split(' ')
            except ValueError:
                first_name = name
                last_name = None
            user, created = User.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                company_name=company,
                job_title=position,
                email=email,
                telegram_id=update.effective_user.id,
                telegram_username=telegram,
                questionnaire_filled=True
            )
            if created:
                context.bot.send_message(
                        chat_id=update.effective_message.chat_id,
                        text='Опрос окончен, спасибо за участие!',
                        reply_markup=create_greetings_menu()
                        )
        except Exception as err:
            print(err)
            answers = user_data['answers']
            context.bot.send_message(
                        chat_id=update.effective_message.chat_id,
                        text=f'Ваша анкета уже есть в базе данных{answers}',
                        reply_markup=create_greetings_menu()
                        )
        return HANDLE_MENU


def read_poll_questions():
    with open('questions_to_clients.txt', 'r', encoding='utf8') as file_handler:
        poll_questions = json.load(file_handler)
    return poll_questions


def clean_message(update: Update, context: CallbackContext):
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def handle_error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""


def end_conversation(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Пока!'
        )
    return ConversationHandler.END
