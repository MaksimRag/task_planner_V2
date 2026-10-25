import db
from werkzeug.security import generate_password_hash

def init_database():
    print("Удаление старых таблиц (если они есть)...")
    db.request_processing("DROP TABLE IF EXISTS tasks CASCADE;")
    db.request_processing("DROP TABLE IF EXISTS projects CASCADE;")
    db.request_processing("DROP TABLE IF EXISTS users CASCADE;")

    print("Создание таблиц...")
    db.create_table_users()
    db.create_table_projects()
    db.create_table_tasks()

    print("Создание тестового пользователя (Логин: demo, Пароль: admin123)...")
    password_hash = generate_password_hash("admin123")
    user_res = db.request_processing(
        "INSERT INTO users (login, password_hash) VALUES (%s, %s) RETURNING id;",
        params=("demo", password_hash), fetch=True
    )
    user_id = user_res['id']
    print(f"Пользователь создан (ID: {user_id})")

    print("Создание проектов...")
    proj1 = db.request_processing(
        "INSERT INTO projects (user_id, title, description) VALUES (%s, %s, %s) RETURNING id;",
        params=(user_id, "Работа", "Рабочие проекты и задачи"), fetch=True
    )['id']
    
    proj2 = db.request_processing(
        "INSERT INTO projects (user_id, title, description) VALUES (%s, %s, %s) RETURNING id;",
        params=(user_id, "Личное", "Домашние дела и планы"), fetch=True
    )['id']

    print("Добавление задач...")
    tasks = [
        (user_id, proj1, "Сверстать главную страницу", "Использовать макет из Figma", "in_progress", "high", "2026-11-01 18:00:00"),
        (user_id, proj1, "Настроить базу данных", "Развернуть PostgreSQL", "done", "medium", "2026-10-20 12:00:00"),
        (user_id, proj1, "Купить домен", "Оплатить на год вперед", "todo", "urgent", "2026-10-24 10:00:00"),
        (user_id, proj2, "Записаться к стоматологу", "Плановый осмотр", "done", "medium", "2026-10-22 10:00:00"),
        (user_id, proj2, "Купить продукты", "Молоко, хлеб, яйца", "todo", "medium", "2026-10-26 19:00:00"),
        (user_id, proj2, "Оплатить коммуналку", "Квитанции за октябрь", "cancelled", "urgent", "2026-10-25 12:00:00"),
    ]

    for t in tasks:
        db.request_processing(
            """INSERT INTO tasks (user_id, project_id, title, description, status, priority, due_date) 
               VALUES (%s, %s, %s, %s, %s, %s, %s);""",
            params=t
        )

    print("Готово! База данных успешно инициализирована.")

if __name__ == "__main__":
    init_database()