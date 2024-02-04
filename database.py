import sqlite3 as sq

db = sq.connect('telgb.db')
cur = db.cursor()

async def start_db():
    with db:
        cur.execute('CREATE TABLE IF NOT EXISTS data '
                    '(tg_id INTEGER, '
                    'article TEXT, '
                    'current_price INTEGER)')
        db.commit()
        print("db started")

async def add_article(tg_id, article, current_price):
    with db:
        if not cur.execute('SELECT tg_id, article FROM data WHERE tg_id = ? AND article = ?', (tg_id, article)).fetchone():
            cur.execute("INSERT INTO data (tg_id, article, current_price) "
                        "VALUES (?, ?, ?)", (tg_id, article, current_price))
            db.commit()
            print("article added")
        else:
            print("this article from that user already is added")