import telebot
from telebot import types
from rembg import new_session, remove
from PIL import Image
import io
import os
import logging
import config

bot = telebot.TeleBot(config.BOT_TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Клавиатура с кнопкой для выбора модели и фона (вынесена отдельно, потому что используется больше 1 раза)
def get_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Сменить модель", callback_data='change_model'))
    markup.add(types.InlineKeyboardButton("🖼 Загрузить фон", callback_data='upload_bg'))
    return markup

# Обработка кнопок inline
@bot.callback_query_handler(func=lambda call: call.data in ['change_model', 'upload_bg'])
def handle_callback(call):
    if call.data == 'change_model':
        choose_model(call.message)
    elif call.data == 'upload_bg':
        bot.send_message(call.message.chat.id, "📤 Пришлите изображение с подписью 'Фон'.")

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    
    bot.send_message(
        message.chat.id,
        "👋 Привет! Просто пришли фото, и я заменю фон.\n"
        "Сейчас установлена модель 'u2net'. Если качество фотографии получилось не таким как хотелось бы, вы всегда можете выбрать другую модель обработки.",
        reply_markup=get_inline_keyboard()
    )





#=================== Модуль работы с моделями ===================

# Хранилище выбора модели для каждого пользователя
user_model_choice = {}

# Клавиатура с кнопками видов моделей
def choose_model(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for model in config.AVAILABLE_MODELS:
        markup.add(types.KeyboardButton(model))
    bot.send_message(
        message.chat.id,
        "🧠 Выберите модель для удаления фона:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, set_user_model)

# Установка модели пользователю
def set_user_model(message):
    model_key = message.text.strip().lower()
    if model_key in config.AVAILABLE_MODELS:
        user_model_choice[message.from_user.id] = config.AVAILABLE_MODELS[model_key]
        bot.send_message(
            message.chat.id,
            f"✅ Модель установлена: {model_key}",
            reply_markup=get_inline_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Такой модели нет. Попробуйте снова через /model",
            reply_markup=types.ReplyKeyboardRemove()
        )






#=================== Модуль работы с фотографиями ===================

# Создание папки для пользовательских фонов
os.makedirs("user_backgrounds", exist_ok=True)

# Функция проверки изображения
def check_image_constraints(image_bytes):
    if len(image_bytes) > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        return f"⚠️ Файл слишком большой! Максимальный размер — {config.MAX_FILE_SIZE_MB}MB."

    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        if width > config.MAX_WIDTH or height > config.MAX_HEIGHT:
            return f"⚠️ Слишком большое разрешение! Максимум: {config.MAX_WIDTH}x{config.MAX_HEIGHT}px. У тебя: {width}x{height}px."
    except Exception as e:
        return f"⚠️ Не удалось прочитать изображение: {e}"

    return None

# Обработка загрузки фото и пользовательского фона
@bot.message_handler(content_types=['photo'])
def handle_background_upload(message):
    if message.caption and message.caption.lower() == 'фон':
        try:
            if message.photo:
                file_info = bot.get_file(message.photo[-1].file_id)
            elif message.document:
                file_info = bot.get_file(message.document.file_id)
            else:
                return
            downloaded_file = bot.download_file(file_info.file_path)
            path = f"user_backgrounds/{message.from_user.id}.png"
            with open(path, "wb") as f:
                f.write(downloaded_file)
            bot.send_message(message.chat.id, "✅ Новый фон успешно загружен!")
        except Exception as e:
            logging.exception("Ошибка при загрузке пользовательского фона")
            bot.send_message(message.chat.id, f"❌ Не удалось загрузить фон: {e}")
        return
    else:
        msg = bot.send_message(message.chat.id, "📥 Загружаю фото и удаляю фон...")

    try:
        # Получаем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Проверка размеров
        error_msg = check_image_constraints(downloaded_file)
        if error_msg:
            bot.send_message(message.chat.id, error_msg)
            bot.delete_message(message.chat.id, msg.message_id)
            return

        # Получение модели пользователя
        model_name = user_model_choice.get(message.from_user.id, config.DEFAULT_REMBG_MODEL)
        session = new_session(model_name)

        removed_bg = remove(downloaded_file, session=session)
        no_bg_image = Image.open(io.BytesIO(removed_bg)).convert("RGBA")

        # Пользовательский фон или дефолтный
        user_bg_path = f"user_backgrounds/{message.from_user.id}.png"
        if os.path.exists(user_bg_path):
            background = Image.open(user_bg_path).convert("RGBA")
        else:
            background = Image.open(config.BACKGROUND_IMAGE_PATH).convert("RGBA")
        background = background.resize(no_bg_image.size)

        result_image = Image.alpha_composite(background, no_bg_image)

        # Отправка результата
        output = io.BytesIO()
        result_image.save(output, format="PNG")
        output.seek(0)

        # Кнопки под результатом
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 Сменить модель", callback_data='change_model'),
            types.InlineKeyboardButton("🖼 Заменить фон", callback_data='upload_bg')
        )

        bot.send_photo(message.chat.id, output, reply_markup=markup)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        logging.exception(f"Ошибка при обработке изображения от пользователя {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка. Уже исправляем!")


    

# Запуск бота
bot.infinity_polling()
