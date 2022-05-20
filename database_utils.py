import aiosqlite

conn = aiosqlite.connect("database.db")


async def create_users_table():
    await conn.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    is_active BOOLEAN,
                    is_bot BOOLEAN,
                    username VARCHAR(33),
                    first_name VARCHAR,
                    last_name VARCHAR,
                    )""")


async def add_user():
    values = (3, True, False, "@Al", "Al", "Sal")
    await conn.execute("""INSERT INTO users VALUES (?,?,?,?,?,?)""", values)
    await conn.commit()


async def select_user():
    async with conn.execute("SELECT * FROM some_table") as cursor:
        async for row in cursor:
            print(row)


if __name__ == '__main__':
    create_users_table()
    conn.run()
