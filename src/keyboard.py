from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура бота"""
    keyboard_main_menu = ReplyKeyboardMarkup(resize_keyboard= True,
                                            one_time_keyboard= True)
    kb1Start = KeyboardButton("/help")
    kb2Start = KeyboardButton("/download_video")
    kb3Start = KeyboardButton("/description")
    keyboard_main_menu.add(kb1Start, kb2Start, kb3Start)
    
    return keyboard_main_menu

def download_video_ikb() -> InlineKeyboardMarkup:
    """Инлайн клавиатура, которая будет срабатывать после того как пользователь скачает видео"""
    inlineKeyboard_question = InlineKeyboardMarkup(row_width= 2)
    kb1Like = InlineKeyboardButton(text= '👍🏻',
                                callback_data = 'LikeAnswer')
    kb2Govno = InlineKeyboardButton(text= '💩',
                                callback_data = 'DislikeAnswer')

    inlineKeyboard_question.add(kb1Like, kb2Govno)

    return inlineKeyboard_question

def keyboard_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка "ОТМЕНА❌", которая будет появляться только когда работает команда download_video"""
    keyboard_cancel = ReplyKeyboardMarkup(resize_keyboard= True)
    kb1Cancel = KeyboardButton('ОТМЕНА❌')
    keyboard_cancel.add(kb1Cancel)

    return keyboard_cancel
    