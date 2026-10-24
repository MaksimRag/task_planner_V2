import db

print("=== 1. ИНФОРМАЦИЯ О БАЗЕ ===")
# Смотрим, к какой базе мы вообще подключены
db_info = db.request_processing("SELECT current_database(), current_user, inet_server_port();", fetch=True)
print("База:", db_info['current_database'])
print("Пользователь:", db_info['current_user'])
print("Порт:", db_info['inet_server_port'])

print("\n=== 2. ВСТАВЛЯЕМ ПОЛЬЗОВАТЕЛЯ ===")
# Вставляем напрямую через функцию
result = db.insert_into_user("debug_user_999", "hash_123")
print("Результат вставки:", result)

print("\n=== 3. ЧИТАЕМ СРАЗУ ПОСЛЕ ВСТАВКИ ===")
# Пытаемся найти этого пользователя
user = db.request_processing("SELECT id, login FROM users WHERE login = 'debug_user_999';", fetch=True)
print("Найденный пользователь:", user)

print("\n=== 4. СМОТРИМ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ===")
all_users = db.request_processing("SELECT id, login FROM users;", fetch=True, many=True)
print("Все пользователи:", all_users)

