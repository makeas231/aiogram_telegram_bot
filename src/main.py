import logging
import random
import os

from pytube import YouTube
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import NetworkError

from keyboard import keyboard_main_menu, inlineKeyboard_question, keyboard_cancel
from other import is_youtube_url, convert_time
from config import TOKEN_API


class ProfileState(StatesGroup):
    """Класс состояния"""
    url_video = State()


# Создаем экземпляры класса Bot и Dispatcher и MemoryStorage
storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage= MemoryStorage())

# Создаем пользовательский лог и задаем уровень логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# настройка обработчика и форматировщика для logger
handler = logging.FileHandler(f"tgBot.log", mode='a', encoding='utf-8')
formatter = logging.Formatter("%(asctime)s  %(levelname)s  %(message)s")

# добавление форматировщика к обработчику
handler.setFormatter(formatter)
# добавление обработчика к логгеру
logger.addHandler(handler)

# Словарь в котором будут храниться все активные пользователи(и видео которое они скачивают(ли))
active_users = {}

HELP_TEXT = f"""
<b>/start</b> - Первоначальный запуск бота.
<b>/help</b> - Помощь.
<b>/description</b> - Описание бота.
<b>/download_video</b> - Основной функционал бота, используя его можно скачивать видео.
"""

DESCTIPTION_TEXT = f"""
Функционал данного бота максимально простой, используя команду /download_video
ты можешь скачивать любое видео с Youtube. Если ты запутался, то можешь использовать
команду /help, чтобы посмотреть все доступные команды.
"""

async def on_startup(_):
    """Асинхронная функция которая будет запускаться во время начала работы бота"""
    print("Телеграмм бот был успешно запущен!")
                     
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """Хендлер для обработки команды /start"""
    username = message.from_user.username
    active_users[f'last_down_video_{message.from_user.username}'] = None
    
    # Если пользователь не ввел свое имя, присваиваем ему значение "Друг"
    if username == None:
        username = 'Друг'

    START_TEXT = f"""Приветствую <b>{username}</b>
С помощью данного телеграмм бота, ты сможешь скачивать бесплатно любые видео видео с Youtube.
В случае ошибки, сразу пиши создателю бота - @makcum6"""
    await bot.send_sticker(chat_id=message.chat.id,
                        sticker='CAACAgIAAxkBAAEIf5NkMHhR_xuJLsLEKwP_g0QDaBLIXAACzhkAAlPHqEkTwUAIA_EBDy8E')
    await bot.send_message(chat_id=message.chat.id,
                        text=START_TEXT,
                        parse_mode='HTML',
                        reply_markup= keyboard_main_menu)
    await message.delete()

    logging.info(f"""{username} ----- Активировал функцию /start
Активные пользователи на данный момент ----> {active_users}""")

@dp.message_handler(commands=["download_video"])
async def download_video(message: types.Message):
    await bot.send_message(chat_id= message.chat.id,
                        text='Чтобы скачать видео, скинь мне ссылку на ролик!',
                        reply_markup= keyboard_cancel)
    await ProfileState.url_video.set() # Включаем состояние "url_video"

    logging.info(f"""{message.from_user.username} ----- Активировал функцию /download_video
Активные пользователи на данный момент ----> {active_users}""")

@dp.message_handler(content_types=['text'], state=ProfileState.url_video)
async def url_video_state(message: types.Message, state: FSMContext):
    url = message.text
    if url == 'ОТМЕНА❌':
        await bot.send_message(chat_id= message.chat.id,
                        text= "Выход в главное меню...",
                        reply_markup= keyboard_main_menu)
        await state.finish() # Если пользователь нажмет на кнопку ОТМЕНА❌, то возвращаемся в главное меню и выходим из состояния
    else:
        try:
            async with state.proxy() as data:
                data['url_video'] = url

            if is_youtube_url(url) == False:
                await message.answer(f"""
URL - {url} ------> 
Данная ссылка не ведет на сайт YouTube, попробуй ввести другую ссылку""")
            else:                         
                yt = YouTube(url)
                await message.answer(text="Идет скачивание видео... Это может занять некоторое время👻")
                video = yt.streams.get_highest_resolution()

                # Название файла будет таким же как его название на YouTube
                sent_video = f"{yt.title}.mp4" 
                video.download(filename= sent_video)

                # Добавляем пользователя скачавшего видео в словарь активных пользователй
                active_users[f'last_down_video_{message.from_user.username}' ] = url
            
                logging.info(f"""{message.from_user.username} ----- начал скачивание видео {url}
Активные пользователи на данный момент ----> {active_users}""")
                
                with open(sent_video, 'rb') as video_file:
                    await bot.send_video(chat_id=message.chat.id,
                                        video=video_file,
                                        caption= f"""
🎥 Название - {yt.title}
👥 Автор - {yt.author}

🧑🏻‍💻 Было опубликованно - {str(yt.publish_date)[0:10]} 
👀 Просмотров - {yt.views}
👮🏻‍♀️ Продолжительность - {convert_time(yt.length)}""")

                os.remove(sent_video) # Удаляем скачанный файл после отправки

                await bot.send_message(chat_id = message.chat.id,
                                        text= """Вот твое видео, а это инструкция для скачивания:
<b>ДЛЯ ПК:</b>
Нажми на видео которое тебе пришло, правой кнопкой мыши, и из предложенных тебе вариантов выбери
<b>Save As...(Сохранить как)</b> После, у тебя откроется окно проводника,
в котором тебе нужно будет сохранить видео в нужную тебе директорию.
<b>ДЛЯ ТЕЛЕФОНОВ (Android, IOS):</b> 
У видео которое тебе пришло, справа вверху будет три точки, нажми на них, и из всех вариантов выбери
<b>Сохранить в галерею.</b>. И видео скачается тебе в галерею.""",
                parse_mode= 'HTML',
                reply_markup = keyboard_main_menu)
                # После завершения работы команды download_video, возвращаем кнопки главного меню
                
                logging.info(f"{message.from_user.username} ----- успешно скачал видео✅")

                await bot.send_message(chat_id= message.chat.id,
                                        text="Спасибо что использовал нашего бота, как тебе сам бот?",
                                        reply_markup= inlineKeyboard_question)
                await state.finish()

        except NetworkError as ne:
            await bot.send_message(chat_id= message.chat.id,
                                    text= """
На данный момент времени, можно скачивать видео только до 30 мбит,
к сожалению ваше видео превышает этот лимит, но не расстраивайся,
это только тестовая часть бота :(, данный лимит будет расширен в скором времени!!!""",
reply_markup= keyboard_main_menu)
            await state.finish()

            logging.info(f"""
{message.from_user.username} ----- во время скачивание видео произошла ошибка❌  --- КОД ОШИБКИ:
{ne}                         """)
        except Exception as er:
            await bot.send_message(chat_id= message.chat.id,
                                        text= f"""
Ой... Произошла не предвиденная ошибка :(
Код ошибки ----> {er}, для решения проблемы напиши создателю @makcum6""",
reply_markup= keyboard_main_menu)
            await state.finish()

            logging.info(f"""
{message.from_user.username} ----- во время скачивание видео произошла ошибка❌ --- КОД ОШИБКИ:
{er}""")

@dp.message_handler(commands= ['help'])
async def help_command(message: types.Message):
    """Хендлер для команды help""" 
    await bot.send_sticker(chat_id = message.chat.id,
                        sticker= 'CAACAgIAAxkBAAEIkX5kOERfeEDieT-rpQbxFb_6Xh_0GgACGhkAAkdGqUnDFGIOpJAMEy8E')
    await bot.send_message(chat_id = message.chat.id,
                        text = HELP_TEXT,
                        parse_mode = 'HTML')
    
    logging.info(f"""{message.from_user.username} ----- Активировал функцию /help
Активные пользователи на данный момент ----> {active_users}""")

@dp.message_handler(commands= ['description'])
async def description_command(message: types.Message):
    """Хендлер для обработки команды /description"""
    await bot.send_sticker(chat_id = message.chat.id,
                        sticker= 'CAACAgIAAxkBAAEInNNkPM75NTAkdlcoq9odZQUB0XLCeQAC5hUAAmRYqEnLZGWnzmR7-y8E')
    await bot.send_message(chat_id = message.chat.id,
                        text= DESCTIPTION_TEXT,
                        parse_mode= 'HTML')
    
    logging.info(f"""{message.from_user.username} ----- Активировал функцию /description
    Активные пользователи на данный момент ----> {active_users}    """)

@dp.message_handler()
async def noy_name_message(message: types.Message):
    """Хендлер для всех осталаных команд"""
    # Cписок ответов на неизвестные сообщения
    list_of_answer = [
"Извините, я не понимаю, о чем вы говорите. Пожалуйста, попробуйте сформулировать свой запрос по-другому.",
"ЭЭЭЭ, начальника, я тебя не понимаю, активирую команду /help",
"Простите, я не знаю, как на это ответить. Можете задать мне другой вопрос?",
"К сожалению, я не обладаю достаточной информацией, чтобы ответить на ваше сообщение. Можете задать мне другой вопрос?",
"Я умею отвечать только на определенные команды. Пожалуйста, введите одну из доступных команд или задайте мне вопрос по теме, на которую я специализируюсь.",
"Извините, я не могу ответить на ваше сообщение в данный момент. Попробуйте позже или свяжитесь с моим разработчиком, чтобы уточнить причину проблемы.",
"Пожалуйста, используйте одну из доступных команд или задайте мне вопрос по теме, которую я могу обработать. Список доступных команд можно получить, написав /help.",
"Я не понимаю вашего сообщения. Пожалуйста, опишите свой запрос более подробно или свяжитесь с моим разработчиком, чтобы получить помощь.",
"К сожалению, я не могу обработать ваш запрос. Попробуйте сформулировать его по-другому или задайте мне другой вопрос.",
"Ой... Мне кажется я тебя не понимаю, для помощи, активируй команду /help",
"Давай поговорим на другие темы? Посмотри в меню команды на которые я умею отвечать"]
    if message.text != ['/help', '/description', '/download_video', '/start']:
        random_offer = random.choice(list_of_answer) # Достаем рандомное предложение из списка
        await message.answer(text= random_offer)

    logging.info(f"""{message.from_user.username} ----- {message.text}
Пользователь ввел неизвестную команду""")

@dp.callback_query_handler()
async def callback_data(callback: types.CallbackQuery):
    """Калбек хендлер, для обработки калбеков"""
    if callback.data == 'LikeAnswer':
        await bot.send_sticker(chat_id= callback.message.chat.id,
                               sticker='CAACAgIAAxkBAAEIl6FkOqw2RveQvmtnYbh9nh-9Ks3K3QACSSUAAsO1AUmg5-gksKmnmS8E')
        await bot.send_message(chat_id= callback.message.chat.id,
                               text= 'Спасибо :)')
    if callback.data == 'GovnoAnswer':
        await bot.send_message(chat_id= callback.message.chat.id,
                               text= 'Очень жалко :(, если у тебя есть какие то заметки или идеи по улучшению бота, напиши разработчику @makcum6')

if __name__ == '__main__':
    executor.start_polling(dispatcher= dp,
                           skip_updates= True,
                           on_startup= on_startup)
