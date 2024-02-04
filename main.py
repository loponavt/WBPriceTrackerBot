import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Message, ReplyKeyboardMarkup
import database as db
import requests
from fake_useragent import UserAgent
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot=bot)


async def get_item_data(article: str):
    headers = {'user-agent': UserAgent(use_external_data=True).chrome}
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
                answer['price'] = round(product.get('salePriceU')/100)
                answer['supplier'] = product.get('supplier')
                review_rating = product.get('reviewRating')
                # TODO хорошо бы возвращать еще и картинку

    except requests.exceptions.HTTPError:
        logging.warning(
            'Проблемы с получением данных, '
            f'артикул {article}')
    except AttributeError as e:
        logging.error(
            'Ошибка при обработке данных '
            f'для артикула {article}: {e}')
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
    else:
        answer = f'{item_name}\n{item_supplier}\n{item_price} ₽'
    await message.answer(answer)
    if answer != 'Не могу найти такой артикул':
        await db.add_article(message.from_user.id, message.text, item_price)

async def main():
    await db.start_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())