import asyncio
import logging

import requests
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fake_useragent import UserAgent
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv('WB_TOKEN'))
working_dir = os.getenv('WB_WORKING_DIR')
import database as db

file_logger = logging.getLogger('file_logger')
console_logger = logging.getLogger('console_logger')

dp = Dispatcher(bot=bot)
builder = InlineKeyboardBuilder()
builder.add(types.InlineKeyboardButton(text='Перестать отслеживать', callback_data='delete_item'))

async def get_item_data(article: str) ->  dict[str, str | int]:
    """
    Возвращает имя, цену и продавца по артикулу товара или None в если запрос не прошел
    :param article: артикул товара
    :return:
    """
    answer = {'name': '', 'supplier': '', 'price': 0}
    headers = {'user-agent': UserAgent().chrome}
    try:
        response = requests.get(url=f'https://card.wb.ru/cards/detail?spp=18&locale=ru&lang=ru&curr=rub&nm={article}',
                                headers=headers)
        json_data = response.json().get('data')
        if json_data:
            for product in json_data.get('products'):
                answer['name'] = product.get('name')
                answer['price'] = round(product.get('salePriceU') / 100)
                answer['supplier'] = product.get('supplier')
    except AttributeError as e:
        file_logger.error(f'Ошибка при обработке данных для артикула {article}: {e}')
    except requests.exceptions as ex:
        file_logger.error(f'Проблемы с получением данных: {ex}')
    return answer

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer(f'Привет, {message.from_user.first_name}\n'
                         f'Для отслеживания цены товара, пришли мне его артикул')


@dp.message(F.text)
async def message_handler(message: Message):
    item_data = await get_item_data(message.text)
    item_name = item_data['name']
    item_supplier = item_data['supplier']
    item_price = item_data['price']

    if item_data['name'] == '':
        file_logger.info(f'{message.from_user.first_name} {message.from_user.last_name}'
                         f'@{message.from_user.username}: {message.text}')
        await message.answer('Не могу найти такой артикул')
    else:
        if await db.add_article(message.from_user.id, message.text, item_price,
                             message.from_user.first_name, message.from_user.last_name, message.from_user.username):

            await message.answer(f'`{message.text}`\n'
                                 f'{item_name}\n'
                                 f'{item_supplier}\n'
                                 f'{item_price} ₽\n'
                                 f'Товар добавлен', parse_mode='MARKDOWN', reply_markup=builder.as_markup())
        else:
            await message.answer('Этот артикул уже был добавлен')

@dp.callback_query()
async def callback_query_keyboard(callback: types.CallbackQuery):
    article = callback.message.text[:callback.message.text.find('\n')]
    await db.remove_article(callback.from_user.id, article)
    await callback.message.answer(f'Артикул `{article}` больше не отслеживается', parse_mode='MARKDOWN')
    await callback.answer()

async def write_to_user(chat_id: int, text: str):
    await bot.send_message(chat_id, text, parse_mode='MARKDOWN', reply_markup=builder.as_markup())

async def start_looper():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(db.check_price, trigger='interval', seconds=60)
    scheduler.start()
    file_logger.info('looper started')
    console_logger.info('looper started')

async def main():
    await asyncio.gather(db.start_db(),
                         start_looper(),
                         dp.start_polling(bot))


if __name__ == '__main__':
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] >> %(message)s',
                                  datefmt='%d.%m.%y %H:%M:%S')
    file_logger.setLevel(logging.INFO)
    console_logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    console_logger.addHandler(sh)

    if not os.path.isdir(f'{working_dir}/log_dir'):
        os.makedirs(f'{working_dir}/log_dir')
        console_logger.info('create log_dir')

    fh = logging.FileHandler(f'{working_dir}/log_dir/logi.log')
    fh.setFormatter(formatter)
    file_logger.addHandler(fh)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

