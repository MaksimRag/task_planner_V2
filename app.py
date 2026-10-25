from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import db


app = Flask(__name__)
app.secret_key = "замените-на-случайную-строку"


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'created')
    view = request.args.get('view', 'list')

    tasks = db.get_tasks_filtered(user_id, search=search, sort=sort)
    
    # Получаем проекты, чтобы знать, есть ли они вообще
    projects = db.get_projects_by_user(user_id)

    if view == 'board':
        grouped = {
            'todo':        [t for t in tasks if t['status'] == 'todo'],
            'in_progress': [t for t in tasks if t['status'] == 'in_progress'],
            'done':        [t for t in tasks if t['status'] == 'done'],
        }
        return render_template('index.html',
                               login=session['login'],
                               tasks=tasks,
                               projects=projects, # <--- ПЕРЕДАЕМ ПРОЕКТЫ
                               grouped=grouped,
                               search=search, sort=sort, view=view)

    return render_template('index.html',
                           login=session['login'],
                           tasks=tasks,
                           projects=projects, # <--- ПЕРЕДАЕМ ПРОЕКТЫ
                           search=search, sort=sort, view=view)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_value = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        if not login_value or not password:
            return render_template('login.html', error='Заполните все поля')

        users = db.get_all_users_with_hash()
        user = next((u for u in users if u['login'] == login_value), None)

        if user is None or not check_password_hash(user['password_hash'], password):
            return render_template('login.html', error='Неверный логин или пароль')

        session['user_id'] = user['id']
        session['login'] = user['login']

        return redirect(url_for('index'))

    message = 'Аккаунт создан. Теперь войдите.' if request.args.get('registered') else None
    return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_value = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not login_value or not password:
            return render_template('register.html', error='Заполните все поля')

        if len(login_value) < 4:
            return render_template('register.html', error='Логин должен быть не короче 4 символов')

        if len(password) < 6:
            return render_template('register.html', error='Пароль должен быть не короче 6 символов')

        if password != password_confirm:
            return render_template('register.html', error='Пароли не совпадают')

        users = db.get_all_users()
        if any(u['login'] == login_value for u in users):
            return render_template('register.html', error='Такой логин уже занят')

        password_hash = generate_password_hash(password)
        db.insert_into_user(login_value, password_hash)

        return redirect(url_for('login', registered=1))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ПРОСМОТР ЗАДАЧИ ---
@app.route('/tasks/<int:task_id>')
def task_detail(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task = db.get_task_full(task_id, user_id)
    
    if task is None:
        abort(404)

    # Получаем имя проекта для красивого вывода
    project_name = None
    if task['project_id']:
        project = db.request_processing(
            "SELECT title FROM projects WHERE id = %s;", 
            params=(task['project_id'],), fetch=True
        )
        if project:
            project_name = project['title']

    return render_template('task_detail.html', task=task, project_name=project_name)


# --- РЕДАКТИРОВАНИЕ ЗАДАЧИ ---
@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task = db.get_task_full(task_id, user_id)
    
    if task is None:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'todo')
        due_date = request.form.get('due_date') or None

        if not title:
            return render_template('task_form.html', task=task, error='Название обязательно')

        db.update_task(task_id, user_id, title, description, priority, due_date, status)
        return redirect(url_for('task_detail', task_id=task_id))

    return render_template('task_form.html', task=task)


@app.route('/tasks/new', methods=['GET', 'POST'])
def new_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        due_date = request.form.get('due_date') or None

        if not title or not project_id:
            projects = db.get_projects_by_user(user_id)
            return render_template('task_form.html',
                                   projects=projects,
                                   error='Заполните название и проект')

        result = db.insert_into_task(user_id, project_id, title, description, priority, due_date)
        return redirect(url_for('task_detail', task_id=result['id']))

    projects = db.get_projects_by_user(user_id)
    return render_template('task_form.html', projects=projects)


@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Читаем next из GET (при переходе) или из POST (при отправке формы)
    next_page = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title:
            return render_template('project_form.html', error='Название обязательно')

        db.insert_into_project(user_id, title, description)
        
        # ВОТ ЭТА ПРОВЕРКА ВОЗВРАЩАЕТ ОБРАТНО
        if next_page == 'new_task':
            return redirect(url_for('new_task'))
            
        return redirect(url_for('projects_list'))

    return render_template('project_form.html')


@app.route('/projects')
def projects_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    projects = db.get_projects_by_user(user_id)
    
    projects_with_tasks = []
    for p in projects:
        tasks = db.get_tasks_by_project(p['id'])
        projects_with_tasks.append({
            'project': p,
            'tasks': tasks
        })

    return render_template('projects.html', projects=projects_with_tasks, login=session.get('login'))


@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    project = db.request_processing(
        "SELECT id, user_id, title, description FROM projects WHERE id = %s AND user_id = %s;",
        params=(project_id, user_id), fetch=True
    )
    
    if not project:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title:
            return render_template('project_form.html', project=project, error='Название обязательно')

        db.update_project(project_id, user_id, title, description)
        return redirect(url_for('projects_list'))

    return render_template('project_form.html', project=project)


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task_route(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db.delete_task(task_id, session['user_id'])
    
    return redirect(url_for('index'))


@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project_route(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db.delete_project(project_id, session['user_id'])
    
    # После удаления возвращаем на страницу со списком проектов
    return redirect(url_for('projects_list'))








if __name__ == '__main__':
    app.run(debug=True)