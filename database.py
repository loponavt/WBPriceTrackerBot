import sqlite3 as sq
import main

db = sq.connect('telgb.db', check_same_thread=False)
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
    with db:
        if not cur.execute('SELECT tg_id, article FROM data WHERE tg_id = ? AND article = ?', (tg_id, article)).fetchone():
            cur.execute("INSERT INTO data (tg_id, article, price) "
                        "VALUES (?, ?, ?)", (tg_id, article, price))
            db.commit()
            main.file_logger.info(f"{article} added by {first_name} {last_name} {username}")
            return True
        else:
            main.file_logger.info("this article from that user already added")
            return False

async def remove_article(tg_id, article):
    with db:
        if cur.execute('SELECT tg_id, article FROM data WHERE tg_id = ? AND article = ?',
                           (tg_id, article)).fetchone():
            cur.execute("DELETE FROM data WHERE tg_id = ? AND article = ?", (tg_id, article,))
            db.commit()

async def price_checker():
    with db:
        for data in cur.execute('SELECT article, price, tg_id FROM data').fetchall():
            article = data[0]
            price_in_table = data[1]
            tg_id = data[2]
            answer = await main.get_item_data(article)
            item_name = answer['name']
            supplier = answer['supplier']
            price = answer['price']
            if price == 0: # если какие-то проблемы и парсер не получил инфу с вб
                continue
            if price_in_table>price:
                difference = price_in_table-price
                percent = round(difference/price_in_table*100)
                await main.write_to_user(tg_id, f"`{article}`\n{item_name}\n{supplier}\n"
                                         f"{price_in_table} ---> {price}\n"
                                         f"-{difference}₽ (-%{percent})")
                cur.execute("UPDATE data SET price = ? WHERE article = ?",
                            (price, article))
                db.commit()