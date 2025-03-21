# Telegram-бот для удаления и замены фона на изображении

Выполнил Орлов Артём

Данный бот позволяет пользователю отправить фотографию, с которой автоматически удаляется фон, а затем подставляется шаблонный или пользовательский.

## Основные возможности:

- Принимает изображение от пользователя.
- Удаляет фон с помощью библиотеки `rembg`.
- Заменяет фон на заранее подготовленный шаблон.
- Позволяет выбрать модель удаления фона.
- Поддерживает загрузку своего пользовательского фона.
- Позволяет сменить модель или фон после обработки изображения.
- Отправляет обработанное изображение обратно пользователю в формате PNG.
---
## Используемые технологии

- **Python 3.10+**
- **Telebot** — работа с Telegram Bot API.
- **rembg** — удаление фона с изображений.
- **Pillow (PIL)** — работа с изображениями.
- **logging** — логирование ошибок и событий.
---
## Структура проекта
Clean_back_bot.py — основной скрипт бота
config.py — конфигурационные параметры
bot.log — файл для логгирования ошибок
white-background.jpg — шаблон фона по умолчанию
requirements.txt — список фреймворков, для ускорения установки

---
## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Укажите токен бота в config.py

4. Запустите бота:
```bash
python Clean_back_bot.py
```
5. Зайдите в телеграмм и запустите бота, которого вы создали, командой /start
