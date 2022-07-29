from email import message
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
from bot.models import User, Meetup, Stream, Report, Donation, Question,Block
import json
import logging
START, HANDLE_MENU, HANDLE_PROGRAMS,\
HANDLE_FORM, HANDLE_QUESTIONS, HANDLE_FLOW,\
    HANDLE_BLOCK, CLOSE = range(8)

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
        product_button = [InlineKeyboardButton(product.__str__(), callback_data=f'{callbackdata}_{product.id}')]
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


def stream_handle_menu(update: Update, context: CallbackContext) -> None:
    clean_message(update, context)
    query = update.callback_query.data
    entity, stream_id = query.split('_')
    if entity == 'reports':
        stream = Stream.objects.get(id=int(stream_id))
        blocks = stream.blocks.all()
        program = ('blockreport', blocks)
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Выберите интересующий вас блок докладов',
            reply_markup=create_menu(program)
        )
        return HANDLE_BLOCK
    elif entity == 'questions':
        # TODO
        stream = Stream.objects.get(id=int(stream_id))
        blocks = stream.blocks.all()
        program = ('blockquestions', blocks)
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Выберите интересующий вас блок, где выступает докладчик, которому вы хотите задать вопрос',
            reply_markup=create_menu(program)
        )
        return HANDLE_BLOCK


def handle_block_reports(update: Update, context: CallbackContext):
    clean_message(update, context)
    keyboard = []
    query = update.callback_query.data
    entity, stream_id = query.split('_')
    block = Block.objects.get(id=int(stream_id))
    reports = block.reports.all()
    rep_message = ''
    for report in reports:
        rep_message += form_report_message(report)
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=rep_message,
        reply_markup=reply_markup
    )
    return HANDLE_BLOCK    


def form_report_message(report):
    report_message = f'Время {report.starts_at} - {report.ends_at}\n{report.title}\n{report.speaker}'
    return report_message


def program_handle_menu(update: Update, context: CallbackContext) -> None:
    reports = Report.objects.all()
    streams = [report.block.stream for report in reports]
    current_streams = set(stream for stream in streams if stream.meetup.status == 'OP')
    program = ('reports', current_streams)
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток необходимой программы',
        reply_markup=create_menu(program)
        )
    return HANDLE_FLOW


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
            name, company, position, email = user_data['answers']
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
                telegram_username=update.message.from_user.username,
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
    logger.warning(
        f'Update {update} caused error {context.error},\
        traceback {context.error.__traceback__}'
        )


def end_conversation(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Пока!'
        )
    return ConversationHandler.END
