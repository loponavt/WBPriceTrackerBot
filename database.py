import sqlite3 as sq

db = sq.connect('telgb.db')
cur = db.cursor()

async def start_db():
    print("db started")
    cur.execute('CREATE TABLE IF NOT EXISTS data '
                '(tg_id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'article TEXT, '
                'current_price INTEGER)')
    db.commit()

async def add_user(user_id):
    with db:
        user = cur.execute("SELECT * FROM data WHERE tg_id == {key}".format(key=user_id)).fetchone()
        if not user:
            cur.execute("INSERT INTO data (tg_id) VALUES ({key})".format(key=user_id))
            db.commit()
            print("user added")

async def add_article(tg_id, article, current_price):
    item_to_add = (tg_id, article, current_price)
    with db:
        cur.execute("INSERT INTO data (tg_id, article, current_price) VALUES (?, ?, ?)", item_to_add)
        db.commit()