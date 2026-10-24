import psycopg2


conn_params = {
    "dbname": "task_planner_V2",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": "5432"
}


#################################################### СОЗДАНИЕ ТАБЛИЦ ####################################################

def create_table_users():
    query = """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                login VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
    request_processing(query=query)


def create_table_projects():
    query = """
            CREATE TABLE projects (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
    request_processing(query=query)


def create_table_tasks():
    query = """
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(30) NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled')),
                priority VARCHAR(30) NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
    request_processing(query=query)


#################################################### УДАЛЕНИЕ ТАБЛИЦ ####################################################

def drop_table_users():
    query = """
            DROP TABLE users;
            """
    request_processing(query=query)


def drop_table_projects():
    query = """
            DROP TABLE projects;
            """
    request_processing(query=query)


def drop_table_tasks():
    query = """
            DROP TABLE tasks;
            """
    request_processing(query=query)


#################################################### ИНСЕРТЫ ТАБЛИЦ ####################################################

def insert_into_user(login, password_hash):
    query = """
            INSERT INTO users (login, password_hash)
            VALUES (%s, %s)
            RETURNING id;
            """
    return request_processing(query=query,
                              params=(login, password_hash),
                              fetch=True)


def insert_into_project(user_id, title, description):
    query = """
            INSERT INTO projects (user_id, title, description)
            VALUES (%s, %s, %s)
            RETURNING id;
            """
    return request_processing(query=query,
                              params=(user_id, title, description),
                              fetch=True)


def insert_into_task(user_id, project_id, title, description, priority, due_date):
    query = """
            INSERT INTO tasks (user_id, project_id, title, description, status, priority, due_date, completed_at)
            VALUES (%s, %s, %s, %s, 'todo', %s, %s, NULL)
            RETURNING id;
            """
    return request_processing(query=query,
                              params=(user_id, project_id, title, description, priority, due_date),
                              fetch=True)


#################################################### GET_ALL ####################################################

def get_all_users():
    query = "SELECT id, login, created_at FROM users ORDER BY id;"
    return request_processing(query=query, fetch=True, many=True)


def get_all_users_with_hash():
    query = "SELECT id, login, password_hash, created_at FROM users ORDER BY id;"
    return request_processing(query=query, fetch=True, many=True)


def get_all_projects():
    query = "SELECT id, user_id, title, description, created_at FROM projects ORDER BY id;"
    return request_processing(query=query, fetch=True, many=True)


def get_all_tasks():
    query = """
            SELECT id, user_id, project_id, title, description, status, priority, due_date, completed_at, created_at
            FROM tasks
            ORDER BY created_at DESC;
            """
    return request_processing(query=query, fetch=True, many=True)


#################################################### GET ####################################################

def get_user(user_id):
    query = "SELECT id, login, created_at FROM users WHERE id = %s;"
    return request_processing(query=query, fetch=True, params=(user_id,))


def get_user_with_hash(user_id):
    query = "SELECT id, login, password_hash, created_at FROM users WHERE id = %s;"
    return request_processing(query=query, fetch=True, params=(user_id,))


def get_project(project_id):
    query = "SELECT id, user_id, title, description, created_at FROM projects WHERE id = %s;"
    return request_processing(query=query, fetch=True, params=(project_id,))


def get_projects_by_user(user_id):
    query = """
            SELECT id, user_id, title, description, created_at
            FROM projects
            WHERE user_id = %s
            ORDER BY created_at DESC;
            """
    return request_processing(query=query, params=(user_id,), fetch=True, many=True)


def get_task(task_id):
    query = """
            SELECT id, user_id, project_id, title, description,
                   status, priority, due_date, completed_at, created_at
            FROM tasks
            WHERE id = %s;
            """
    return request_processing(query=query, fetch=True, params=(task_id,))


def get_tasks_by_user(user_id):
    query = """
            SELECT id, user_id, project_id, title, description,
                   status, priority, due_date, completed_at, created_at
            FROM tasks
            WHERE user_id = %s
            ORDER BY
                CASE status
                    WHEN 'todo' THEN 1
                    WHEN 'in_progress' THEN 2
                    WHEN 'done' THEN 3
                    ELSE 4
                END,
                due_date NULLS LAST,
                created_at DESC;
            """
    return request_processing(query=query, params=(user_id,), fetch=True, many=True)


def get_tasks_by_project(project_id):
    query = """
            SELECT id, user_id, project_id, title, description,
                   status, priority, due_date, completed_at, created_at
            FROM tasks
            WHERE project_id = %s
            ORDER BY created_at DESC;
            """
    return request_processing(query=query, params=(project_id,), fetch=True, many=True)


#################################################### НУЖНЫ ПРАВКИ, ЕЩЁ НЕ СМОТРЕЛ ####################################################

def get_tasks_filtered(user_id, search="", sort="created"):
    allowed_sorts = {
        "created":   "t.created_at DESC",
        "due":       "t.due_date ASC NULLS LAST",
        "priority":  "CASE t.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END",
        "title":     "t.title ASC",
    }
    order_by = allowed_sorts.get(sort, "t.created_at DESC")

    sql = """
        SELECT t.id, t.user_id, t.project_id, t.title, t.description,
               t.status, t.priority, t.due_date, t.completed_at, t.created_at,
               p.title AS project_title
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.user_id = %s
    """
    params = [user_id]

    if search:
        sql += " AND t.title ILIKE %s"
        params.append(f"%{search}%")

    sql += f" ORDER BY {order_by};"

    return request_processing(query=sql, params=tuple(params), fetch=True, many=True)


def get_task_full(task_id, user_id):
    query = """
        SELECT id, user_id, project_id, title, description,
               status, priority, due_date, completed_at, created_at
        FROM tasks
        WHERE id = %s AND user_id = %s;
    """
    return request_processing(query=query, params=(task_id, user_id), fetch=True)


def update_task(task_id, user_id, title, description, priority, due_date, status):
    query = """
        UPDATE tasks
        SET title = %s,
            description = %s,
            priority = %s,
            due_date = %s,
            status = %s,
            completed_at = CASE WHEN %s = 'done' THEN COALESCE(completed_at, NOW()) ELSE NULL END
        WHERE id = %s AND user_id = %s;
    """
    request_processing(
        query=query,
        params=(title, description, priority, due_date, status, status, task_id, user_id)
    )


def update_project(project_id, user_id, title, description):
    query = """
            UPDATE projects 
            SET title = %s, description = %s 
            WHERE id = %s AND user_id = %s;
            """
    request_processing(query=query, params=(title, description, project_id, user_id))


def delete_task(task_id, user_id):
    query = "DELETE FROM tasks WHERE id = %s AND user_id = %s;"
    request_processing(query=query, params=(task_id, user_id))


def delete_project(project_id, user_id):
    query = "DELETE FROM projects WHERE id = %s AND user_id = %s;"
    request_processing(query=query, params=(project_id, user_id))

############################################################################################################################################




def request_processing(query, params=None, fetch=False, many=False):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(**conn_params)
        connection.autocommit = True  # <--- ВОТ ЭТА СТРОКА
        cursor = connection.cursor()
        cursor.execute(query, params)

        if fetch:
            rows = cursor.fetchall()
            if not rows:
                return [] if many else None
            columns = [description[0] for description in cursor.description]
            if many:
                return [dict(zip(columns, row)) for row in rows]
            return dict(zip(columns, rows[0]))

        return None

    except Exception as error:
        print(f"Ошибка: {error}")
        return [] if many else None

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
