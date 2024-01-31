import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Message
import requests
from fake_useragent import UserAgent
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Для отслеживания товара, пришлите мне ссылку на него, чел")

def get_item_price(article: str)->str:
    headers = {'user-agent': UserAgent(use_external_data=True).chrome}
    response = requests.get(url=f'https://card.wb.ru/cards/detail'
                                f'?spp=18&locale=ru&lang=ru&curr=rub'
                                f'&nm={article}', headers=headers)
    answer = 'Нет такого артикула'
    try:
        response.raise_for_status()
        json_data = response.json().get('data')
        # print(json_data)
        if json_data:

            for product in json_data.get('products'):
                name = product.get('name')
                price = round(product.get('salePriceU')/100)
                supplier = product.get('supplier')
                review_rating = product.get('reviewRating')
                # TODO хорошо бы возвращать еще и картинку
                answer = f'{name}\n{supplier}\n{price} ₽'

    except requests.exceptions.HTTPError:
        logging.warning(
            'Проблемы с получением данных, '
            f'артикул {article}')
    except AttributeError as e:
        logging.error(
            'Ошибка при обработке данных '
            f'для артикула {article}: {e}'
        )
    return answer

@dp.message(F.text)
async def message_handler(message: Message):
    await message.answer(str(get_item_price(message.text)))

async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())