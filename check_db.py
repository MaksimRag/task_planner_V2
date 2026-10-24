import db

# Смотрим все таблицы users во всех схемах
schemas = db.request_processing("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name = 'users';
""", fetch=True, many=True)

print("Таблицы users в базе:", schemas)

# Смотрим текущую схему поиска (search_path)
path = db.request_processing("SHOW search_path;", fetch=True)
print("Текущий search_path:", path)