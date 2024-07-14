import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, JobQueue
import pytz
from datetime import datetime, timedelta

# Telegram bot token
TOKEN = "7140780192:AAFt49GgymG9szuyVs47XqTbgC7BjQfh9QA"

# List to store reservations
reservations = []

# Maximum number of reservations
MAX_RESERVATIONS = 12

# Admins who automatically reserve places
admins = ["Влад", "Лиза", "Юля"]

# Keyboard buttons
reserve_button = InlineKeyboardButton("Зарезервировать место", callback_data='reserve')
view_list_button = InlineKeyboardButton("Посмотреть список", callback_data='view_list')
cancel_button = InlineKeyboardButton("Отказаться от резервации", callback_data='cancel')

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in reservations:
        context.bot.send_message(chat_id=user_id, text="Вы уже зарезервировали место.")
    else:
        keyboard = InlineKeyboardMarkup([[reserve_button, view_list_button]])
        context.bot.send_message(chat_id=user_id, text="Добро пожаловать! Используйте кнопку ниже, чтобы зарезервировать место или посмотреть список зарезервированных мест.", reply_markup=keyboard)

def reserve(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in reservations:
        context.bot.send_message(chat_id=user_id, text="Вы уже зарезервировали место.")
    elif len(reservations) >= MAX_RESERVATIONS:
        context.bot.send_message(chat_id=user_id, text="Извините, все места уже заняты.")
    else:
        reservations.append(user_id)
        context.bot.send_message(chat_id=user_id, text=f"Место успешно зарезервировано! Осталось {MAX_RESERVATIONS - len(reservations)} свободных мест.")

        # Показываем кнопки "Посмотреть список" и "Отказаться от резервации"
        keyboard = InlineKeyboardMarkup([[view_list_button, cancel_button]])
        context.bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=keyboard)

def list_reservations(update: Update, context: CallbackContext) -> None:
    reserved_members = admins[:]  # Сначала добавляем всех админов
    reserved_members.extend(update.effective_user.first_name for user_id in reservations if user_id not in admins)

    if reserved_members:
        response = "\n".join([f"{i+1}. {member}" for i, member in enumerate(reserved_members)])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Список зарезервированных мест:\n{response}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="На данный момент нет зарезервированных мест.")

    # Показываем кнопки "Зарезервировать место" и "Отказаться от резервации"
    keyboard = InlineKeyboardMarkup([[reserve_button, cancel_button]])
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите действие:", reply_markup=keyboard)

def cancel_reservation(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in reservations:
        context.bot.send_message(chat_id=user_id, text="Вы еще не зарезервировали место.")
    else:
        reservations.remove(user_id)
        context.bot.send_message(chat_id=user_id, text="Резервация отменена.")

        # Показываем кнопку "Зарезервировать место"
        keyboard = InlineKeyboardMarkup([[reserve_button]])
        context.bot.send_message(chat_id=user_id, text="Выберите действие:", reply_markup=keyboard)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.data == 'reserve':
        reserve(update, context)
    elif query.data == 'view_list':
        list_reservations(update, context)
    elif query.data == 'cancel':
        cancel_reservation(update, context)

def update_participants_list(context: CallbackContext):
    global admins
    admins = ["Влад", "Лиза", "Юля"]
    for user_id in reservations:
        context.bot.send_message(chat_id=user_id, text="Список участников был обновлен в этот воскресенье.")

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    job_queue = updater.job_queue

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # Добавляем задачу на еженедельное обновление списка участников по воскресеньям в 4 утра (Берлинское время)
    berlin_tz = pytz.timezone('Europe/Berlin')
    sunday_4am = berlin_tz.localize(datetime.now().replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=(6 - datetime.now().weekday() + 7) % 7))
    job_queue.run_repeating(update_participants_list, interval=timedelta(weeks=1), first=sunday_4am)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
