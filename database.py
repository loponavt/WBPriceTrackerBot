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
        else:
            main.file_logger.info("this article from that user already added")

async def price_checker():
    with db:
        for data in cur.execute('SELECT article, price, tg_id FROM data').fetchall():
            price_in_table = data[1]
            article = data[0]
            tg_id = data[2]
            answer = await main.get_item_data(article)
            item_name = answer['name']
            supplier = answer['supplier']
            if price_in_table>answer['price']:
                await main.write_to_user(tg_id, f"`{article}`\n{item_name}\n{supplier}\n"
                                         f"{price_in_table} ---> {answer['price']}")
                cur.execute("UPDATE data SET price = ? WHERE article = ?",
                            (answer['price'], article))
                db.commit()