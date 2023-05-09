import logging
import random
import os

from pytube import YouTube
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import NetworkError
from aiogram.dispatcher.filters import Text

from keyboard import main_keyboard, download_video_ikb, keyboard_cancel_keyboard
from other import is_youtube_url, convert_time, LIST_OF_ANSWER, HELP_TEXT, DESCTIPTION_TEXT, TEXT_INSTRUCTIONS
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


async def on_startup(_):
    """Асинхронная функция которая будет запускаться во время начала работы бота"""
    print("Телеграмм бот был успешно запущен!")

@dp.message_handler(Text(equals= 'Привет!'))
async def test_equals(message: types.Message):
    """Тестовый фильтр, который будет обрабатывать именно текст
    который будет отсылаться боту, а не команды"""
    await message.answer("И тебе не хварать, друг")

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
                        reply_markup= main_keyboard())
    await message.delete()

    logging.info(f"""{username} ----- Активировал функцию /start
Активные пользователи на данный момент ----> {active_users}""")

@dp.message_handler(commands=["download_video"])
async def download_video(message: types.Message):
    await bot.send_message(chat_id= message.chat.id,
                        text='Чтобы скачать видео, скинь мне ссылку на ролик!',
                        reply_markup= keyboard_cancel_keyboard())
    await ProfileState.url_video.set() # Включаем состояние "url_video"

    logging.info(f"""{message.from_user.username} ----- Активировал функцию /download_video
Активные пользователи на данный момент ----> {active_users}""")

@dp.message_handler(content_types=['text'], state=ProfileState.url_video)
async def url_video_state(message: types.Message, state: FSMContext):
    url = message.text
    if url == 'ОТМЕНА❌':
        await bot.send_message(chat_id= message.chat.id,
                        text= "Выход в главное меню...",
                        reply_markup= main_keyboard())
        await state.finish() # Если пользователь нажмет на кнопку ОТМЕНА❌, то возвращаемся в главное меню и выходим из состояния
    else:
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
                                        text= TEXT_INSTRUCTIONS,
            parse_mode= 'HTML',
            reply_markup = main_keyboard())
                # После завершения работы команды download_video, возвращаем кнопки главного меню
                
            logging.info(f"{message.from_user.username} ----- успешно скачал видео✅")

            await bot.send_message(chat_id= message.chat.id,
                                        text="Спасибо что использовал нашего бота, как тебе сам бот?",
                                        reply_markup= download_video_ikb())
            await state.finish()

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
    if message.text != ['/help', '/description', '/download_video', '/start']:
        random_offer = random.choice(LIST_OF_ANSWER) # Достаем рандомное предложение из списка
        await message.answer(text= random_offer)

    logging.info(f"""{message.from_user.username} ----- {message.text}
Пользователь ввел неизвестную команду""")

@dp.callback_query_handler()
async def callback_data(callback: types.CallbackQuery):
    """Калбек хендлер, для обработки калбеков"""
    if callback.data == 'LikeAnswer':
        await callback.answer("Спасибо :)")
    if callback.data == 'DislikeAnswer':
        await callback.answer("Очень жалко :(, напиши разработчику @makcum6")


if __name__ == '__main__':
    executor.start_polling(dispatcher= dp,
                           skip_updates= True,
                           on_startup= on_startup)
