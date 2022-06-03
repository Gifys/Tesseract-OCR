import logging
from asyncio import sleep

from PIL import Image
import pytesseract

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from config import TOKEN, FSM
from sqlighter import SQLighter


# Чтобы tesseract работал на винде
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\tesseract.exe'

# parse_mode=types.ParseMode.HTML - чтобы можно было ставить теги как в html
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)

# инициализируем соединение с БД
db = SQLighter('db.db')

dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands='start')
async def command_start(message: types.Message):
    await message.reply("<b>Привет! Отправь фото с текстом (не рукописным), чтобы увидеть меня в действие."
                        "\n\nBeta version 1.0\nПоддержка: plz-dont-touch-me@yandex.ru</b>")

    # Добавление пользователя в БД
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

@dp.message_handler(commands='help')
async def command_help(message: types.Message):
    await message.reply("<b>На основе искусственного интеллекта от Google (Teseract OCR) был написан этот бот. "
                        "Работа бота заключается в чтении отправленной фотографии и вывода с нее всего текста. "
                        "К боту подключен база данных для дальнейшей платный подписки. Пока все бесплатно :D"
                        "\n\nBeta version 1.0\nПоддержка: plz-dont-touch-me@yandex.ru</b>")

@dp.message_handler(commands='game')
async def game(message: types.Message):
    await message.answer('Привет, сейчас я запущу кубики...')
    await sleep(1)

    await message.answer('Я кидаю первый!')
    bot_data = await bot.send_dice(message.from_user.id)
    bot_data = bot_data["dice"]["value"]
    await sleep(5)

    user_data = await bot.send_dice(message.from_user.id)
    user_data = user_data["dice"]["value"]
    await sleep(5)

    if bot_data > user_data:
        await message.answer('Вы проиграли, попробуйте еще раз попозже ;(')
    elif bot_data < user_data:
        await message.answer('Сейчас победа за вами, но это не надолго!')
    else:
        await message.answer('Боевая ничья!')

@dp.message_handler(content_types=['photo'])
async def download_photo(message: types.Message):
    await message.reply('Какой язык на этой фотографии?'
                        '\n\nВозможные языки: \nrus - Русский, eng - English')
    await message.photo[-1].download("work_photo.jpg")

    await FSM.language_selection.set()
    # Сделать выбор языка инлайн кнопкой

@dp.message_handler(state=FSM.language_selection)
async def language_selection(message: types.Message, state=FSMContext):
    image = Image.open("work_photo.jpg")
    image = image.convert('1')

    language = message.text.lower()

    async with state.proxy() as data:
        data['language'] = language

    if language == 'rus':
        text = pytesseract.image_to_string(image, lang="rus")
    elif language == 'eng':
        text = pytesseract.image_to_string(image, lang="eng")

    await message.answer(f'Текст с фото: \n{text}')
    await state.finish()
 
@dp.message_handler()
async def response_to_user_message(message: types.Message):
    if message.text == 'admin':
        await message.answer('Ввдите пароль, чтобы зайти под именем администратора')
    else:
        await message.reply('Я был создан для работы с фото, давай каждый будет заниматься тем, что он умеет...')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)