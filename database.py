import sqlite3 as sq
import main

db = sq.connect(f'{main.working_dir}/tb.db', check_same_thread=False)
cur = db.cursor()

async def start_db():
    with db:
        cur.execute('CREATE TABLE IF NOT EXISTS data '
                    '(tg_id INTEGER, '
                    'article TEXT, '
                    'price INTEGER)')
        db.commit()
        main.file_logger.info('db started')
        main.console_logger.info('db_started')

async def add_article(tg_id, article, price, first_name, last_name, username):
    """
    Добавить строку с информацией в БД
    :param tg_id: tg_id юзера
    :param article: артикул
    :param price: текущая  цена
    :param first_name: имя юзера
    :param last_name: фамилия юзера
    :param username: tg username
    :return:
    """
    with db:
        if not cur.execute('SELECT tg_id, article FROM data WHERE tg_id = ? AND article = ?', (tg_id, article)).fetchone():
            cur.execute('INSERT INTO data (tg_id, article, price) '
                        'VALUES (?, ?, ?)', (tg_id, article, price))
            db.commit()
            main.file_logger.info(f'{article} added by {first_name} {last_name} {username}')
            return True
        else:
            main.file_logger.info(f'article {article} from {tg_id} already added')
            return False

async def remove_article(tg_id, article):
    """
    Удалить артикул из БД
    :param tg_id: tg_id юзера
    :param article: артикул
    """
    with db:
        if cur.execute('SELECT tg_id, article FROM data WHERE tg_id = ? AND article = ?',
                           (tg_id, article)).fetchone():
            cur.execute('DELETE FROM data WHERE tg_id = ? AND article = ?', (tg_id, article,))
            main.file_logger.info(f'article {article} delete by {tg_id}')
            db.commit()

async def check_price():
    """
    Проверяет текущую цену всех артикулов в БД и если цена меняется, дергает update_price
    """
    with db:
        for db_string in cur.execute('SELECT article, price, tg_id FROM data').fetchall():
            article = db_string[0]
            db_price = db_string[1]
            tg_id = db_string[2]
            answer = await main.get_item_data(article)
            if answer['price'] == 0: # если какие-то проблемы и парсер не получил инфу с вб
                continue
            if db_price>answer['price']:
                await update_price(article, db_price, tg_id, answer['price'], answer['name'], answer['supplier'])

async def update_price(article: str, db_price: int, tg_id: int, current_price: int, item_name: str, supplier: str):
    """
    Меняет цену в БД и уведомляет пользователя
    :param article: артикул
    :param db_price: цена в БД
    :param tg_id: id юзера
    :param current_price: текущая цена, полученная по API
    :param item_name: наименование товара
    :param supplier: наименование продавца
    """
    cur.execute('UPDATE data SET price = ? WHERE article = ?',
                (current_price, article))
    db.commit()
    difference = db_price - current_price
    percent = round(difference / db_price * 100)
    await main.write_to_user(tg_id, f'`{article}`\n{item_name}\n{supplier}\n'
                                    f'{db_price} ---> {current_price}\n'
                                    f'-{difference}₽ (-%{percent})')
    main.file_logger.info(f'price {article} changed for {tg_id}')