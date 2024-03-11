import asyncio
import logging
from typing import Optional

import requests

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db

from fake_useragent import UserAgent
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot=bot)
file_logger = logging.getLogger('file_logger')
console_logger = logging.getLogger('console_logger')


async def get_item_data(article: str):
    headers = {'user-agent': UserAgent().chrome}
    response = requests.get(url=f'https://card.wb.ru/cards/detail'
                                f'?spp=18&locale=ru&lang=ru&curr=rub'
                                f'&nm={article}', headers=headers)
    answer = {'name': '',
              'supplier': '',
              'price': 0
              }
    try:
        response.raise_for_status()
        json_data = response.json().get('data')
        # print(json_data)
        if json_data:
            for product in json_data.get('products'):
                answer['name'] = product.get('name')
                answer['price'] = round(product.get('salePriceU') / 100)
                answer['supplier'] = product.get('supplier')
                # TODO хорошо бы возвращать еще и картинку но дорого
    except requests.exceptions.HTTPError:
        file_logger.warning(f'Проблемы с получением данных, артикул {article}')
    except AttributeError as e:
        file_logger.error(f'Ошибка при обработке данных для артикула {article}: {e}')
    return answer

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f'Привет {message.from_user.first_name}\n'
                         f'Для отслеживания цены товара, пришли мне его артикул')


@dp.message(F.text)
async def message_handler(message: Message):
    item_data = await get_item_data(message.text)
    item_name = item_data['name']
    item_supplier = item_data['supplier']
    item_price = item_data['price']
    if item_data['name'] == '':
        answer = 'Не могу найти такой артикул'
        file_logger.info(f'{message.from_user.first_name} {message.from_user.last_name} '
                         f'@{message.from_user.username}: {message.text}')
        await message.answer(answer)
    else:
        if await db.add_article(message.from_user.id, message.text, item_price,
                             message.from_user.first_name, message.from_user.last_name, message.from_user.username):
            answer = f'`{message.text}`\n{item_name}\n{item_supplier}\n{item_price} ₽\nТовар добавлен'
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Удалить артикул",
                callback_data=f"delete_item")
            )
            # await message.answer(answer, reply_markup=builder.as_markup(), parse_mode="MARKDOWN")
            await message.answer(answer)
        else:
            answer = f'Этот артикул уже был добавлен'
            await message.answer(answer)

@dp.callback_query()
async def callback_query_keyboard(callback: types.CallbackQuery):
    answer = callback.message.text[:callback.message.text.find("\n")]
    await db.remove_article(callback.from_user.id, answer)
    await callback.message.answer(f'Артикул {answer} больше не отслеживается')
    await callback.answer()

async def write_to_user(chat_id, text: str):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Удалить артикул",
        callback_data=f"delete_item")
    )
    await bot.send_message(chat_id, text, parse_mode="MARKDOWN", reply_markup=builder.as_markup())

async def start_looper():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(db.price_checker, trigger='interval', seconds=10)
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

    if not os.path.isdir('log_dir'):
        os.makedirs('log_dir')
        console_logger.info('create log_dir')

    fh = logging.FileHandler('log_dir/logi.log')
    fh.setFormatter(formatter)
    file_logger.addHandler(fh)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
