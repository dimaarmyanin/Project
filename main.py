from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# Токен вашего бота
TOKEN = "ваш_токен"

# ID администратора (его нужно получить вручную через @userinfobot)
ADMIN_ID = ваш_id  # Замените на ваш реальный ID (числовой)

# Список услуг с эмодзи и ценами
SERVICES = {
    "Уборка квартиры �": 1000, 
    "Ремонт квартиры 🔨": 5000, 
    "Мойка окон 🪟": 1500, 
    "Стрижка газона 🌱": 800, 
    "Сборка мебели 🪑": 2000
}

# Данные пользователя
user_data = {}

# Этапы заказа
STAGES = {
    'address': 'Введите ваш адрес:',
}

# Функция для начала общения с ботом
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Услуги 🛠️", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Привет! Я бот для заказа услуг. Нажмите 'Услуги', чтобы выбрать нужную услугу. 😊", reply_markup=reply_markup)

# Функция для отображения услуг
async def show_services(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(service, callback_data=service)] for service in SERVICES.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()  # Подтверждаем нажатие кнопки
    await update.callback_query.message.edit_text("Выберите одну из услуг 🧰:", reply_markup=reply_markup)

# Функция для обработки выбора услуги
async def handle_service_selection(update: Update, context: CallbackContext) -> None:
    selected_service = update.callback_query.data

    # Проверяем, является ли выбранный элемент услугой
    if selected_service not in SERVICES:
        await update.callback_query.answer()  # Подтверждаем нажатие кнопки
        return  # Выходим, если это не услуга

    price = SERVICES[selected_service]
    
    # Сохраняем выбранную услугу и начальный этап
    user_data[update.callback_query.from_user.id] = {
        'service': selected_service, 'price': price, 'stage': 'address'
    }
    
    await update.callback_query.answer()
    
    # Запрашиваем адрес
    await update.callback_query.message.reply_text(
        f"Вы выбрали услугу: {selected_service} ✅\nЦена: {price} рублей.\nТеперь, пожалуйста, укажите свой адрес."
    )

# Функция для получения адреса
async def get_address(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['stage'] == 'address':
        # Сохраняем адрес
        user_data[user_id]['address'] = update.message.text
        service = user_data[user_id]['service']
        price = user_data[user_id]['price']
        address = user_data[user_id]['address']
        
        # Отправляем запрос администратору, включая user_id
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый заказ:\n\nУслуга: {service}\nЦена: {price} рублей\nАдрес: {address}\n\nПользователь ID: {user_id}\nПользователь: {update.message.from_user.full_name} (@{update.message.from_user.username})\n\nПожалуйста, ответьте пользователю, используя команду /reply <user_id> <текст ответа>."
        )
        
        # Отправить пользователю подтверждение
        await update.message.reply_text(f"Ваш заказ на услугу '{service}' принят! 📝\nЦена: {price} рублей.\nАдрес: {address}\nОжидайте ответа от администратора.")
        
        # Очищаем данные пользователя после завершения
        del user_data[user_id]
    else:
        await update.message.reply_text("Пожалуйста, выберите услугу перед тем, как отправить адрес.")

# Функция для обработки связи с администратором
async def contact_admin(update: Update, context: CallbackContext) -> None:
    # Запрашиваем у пользователя сообщение для администратора
    await update.message.reply_text("Напишите ваше сообщение для администратора:")
    
    # Сохраняем информацию о том, что пользователь хочет связаться с администратором
    user_data[update.message.from_user.id] = {'stage': 'contact_admin'}

# Функция для обработки сообщений пользователя
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверяем, на каком этапе находится пользователь
    if user_id in user_data:
        stage = user_data[user_id].get('stage')

        if stage == 'contact_admin':
            # Отправляем сообщение админу
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Сообщение от пользователя {update.message.from_user.full_name} (@{update.message.from_user.username}):\n\n{update.message.text}"
            )

            # Подтверждаем пользователю отправку
            await update.message.reply_text("Ваше сообщение отправлено администратору. Ожидайте ответа.")

            # Очищаем данные пользователя
            del user_data[user_id]

# Функция для обработки ответа администратора
async def admin_reply(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Только администратор может использовать эту команду.")
        return

    # Проверка, что администратор ввел ID пользователя и текст ответа
    if len(context.args) < 2:
        await update.message.reply_text("Неправильный формат команды. Используйте: /reply <user_id> <текст ответа>")
        return
    
    user_id = context.args[0]  # ID пользователя
    reply_text = " ".join(context.args[1:])  # Текст ответа
    
    try:
        # Отправляем ответ пользователю
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ответ от администратора: {reply_text}"
        )
        await update.message.reply_text(f"Ответ отправлен пользователю с ID {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"Не удалось отправить ответ пользователю с ID {user_id}. Ошибка: {e}")

# Основная функция для запуска бота
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("contact", contact_admin))  # Команда для связи с администратором
    
    # Обработчик нажатия кнопок
    application.add_handler(CallbackQueryHandler(show_services, pattern="services"))
    application.add_handler(CallbackQueryHandler(handle_service_selection))
    
    # Обработчик ввода адреса
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_address))
    
    # Обработчик сообщений пользователя (для связи с администратором)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Команда для администратора /reply
    application.add_handler(CommandHandler("reply", admin_reply, has_args=True))
    
    application.run_polling()

if __name__ == '__main__':
    main()