from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Task
from app.forms import LoginForm, RegistrationForm, TaskForm, DateForm
from flask import Blueprint
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
        return render_template('register.html', title='Register', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Invalid username')
            return redirect(url_for('main.login'))
        if not user.check_password(form.password.data):
            flash('Wrong password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id, valid=True).all()
    currentDateTime = datetime.now()
    '''
    for task in tasks:
        if task.status != 'Completed':
            if task.deadline < currentDateTime:
                task.status = 'Expired'
    db.session.commit()'''
    check_status()
    return render_template('index.html', title='Home', tasks=tasks, currentDateTime=currentDateTime)


@bp.route('/history', methods=['GET'])
def history():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    currentDateTime = datetime.now()
    '''
    for task in tasks:
        if task.deadline < currentDateTime:
            task.status = 'Expired'''''
    check_status()
    return render_template('history.html', tasks=tasks)


from sqlalchemy.exc import SQLAlchemyError  # 导入 SQLAlchemy 的异常类
# routes.py (inside a blueprint folder, e.g., main)
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    form.valid.data = True
    if form.validate_on_submit():
        try:
            title = form.title.data
            description = form.description.data
            repeat = form.repeat.data
            deadline = form.deadline.data
            importance = form.importance.data
            status = form.status.data
            category = form.category.data
            valid = True

            if repeat == 'Everyday':
                start_date = datetime.today().date()
                end_date = deadline.date()
                if end_date < start_date:
                    flash('The date you input has passed!')
                    return redirect(url_for('main.index'))
                for i in range((end_date - start_date).days + 1):
                    current_date = start_date + timedelta(days=i)
                    new_task = Task(
                        user_id=current_user.id,
                        title=title,
                        description=description,
                        repeat='Everyday',
                        deadline=datetime.combine(current_date, deadline.time()),
                        importance=importance,
                        status='Unstarted',
                        category=category,
                        valid=valid
                    )
                    db.session.add(new_task)
            else:
                new_task = Task(
                    user_id=current_user.id,
                    title=title,
                    description=description,
                    repeat=repeat,
                    deadline=deadline,
                    importance=importance,
                    status=status,
                    category=category,
                    valid=valid
                )
                db.session.add(new_task)

            flash('Task added successfully!', 'success')
            check_status()
            db.session.commit()
            return redirect(url_for('main.index'))
        except SQLAlchemyError as e:
            db.session.rollback()  # 回滚数据库会话
            flash('An error occurred while adding the task.', 'error')
            # 可以在这里记录日志 e.g., app.logger.error(str(e))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return render_template('add_task.html', form=form)


@bp.route('/edit_task/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.')
        return redirect(url_for('main.index'))

    form = TaskForm(obj=task)
    form.valid.data = True
    if form.validate_on_submit():
        try:
            task.title = form.title.data
            task.description = form.description.data
            task.deadline = form.deadline.data
            task.importance = form.importance.data
            task.status = form.status.data
            task.category = form.category.data

            flash('Task changed successfully!', 'success')
            check_status()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page == 'main.index':
                return redirect(url_for('main.index'))
            elif next_page == 'main.history':
                return redirect(url_for('main.history'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while updating the task.', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')

    return render_template('edit_task.html', form=form, task=task)


@bp.route('/delete_task/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.author != current_user:
        flash('You do not have permission to delete this task.')
        return redirect(url_for('main.index'))
    db.session.delete(task)
    db.session.commit()
    flash('Your task has been deleted.')
    next_page = request.args.get('next')
    if next_page == 'main.index':
        return redirect(url_for('main.index'))
    elif next_page == 'main.history':
        return redirect(url_for('main.history'))


from sqlalchemy import extract


@bp.route('/completed/<int:id>')
@login_required
def completed(id):
    task = Task.query.get_or_404(id)
    task.status = 'Completed'
    #task.valid = False
    check_status()
    db.session.commit()
    #flash('One task has been completed.')
    return redirect(url_for('main.index'))


@bp.route('/sortByDeadline', methods=['GET', 'POST'])
@login_required
def sortByDeadline():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline).all()
    currentDateTime = datetime.now()
    return render_template('index.html', title='Home', tasks=tasks, currentDateTime=currentDateTime)


def priority(x):
    if x.importance == 'High':
        return 2
    elif x.importance == 'Medium':
        return 1
    elif x.importance == 'Low':
        return 0


@bp.route('/sortByImportance', methods=['GET', 'POST'])
@login_required
def sortByImportance():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    tasks.sort(key=priority, reverse=True)
    currentDateTime = datetime.now()
    return render_template('index.html', title='Home', tasks=tasks, currentDateTime=currentDateTime)


@bp.route('/find_tasks', methods=['GET', 'POST'])
@login_required
def find_tasks_by_date():
    form = DateForm()
    tasks = None
    if form.validate_on_submit():
        try:
            query_date = form.date.data
            tasks = Task.query.filter(
                Task.user_id == current_user.id,
                extract('year', Task.deadline) == query_date.year,
                extract('month', Task.deadline) == query_date.month,
                extract('day', Task.deadline) == query_date.day
            ).all()
            if not tasks:
                flash('No tasks found for the selected date.', 'info')
        except SQLAlchemyError as e:
            flash('An error occurred while querying tasks.', 'error')
            # 可以在这里记录日志 e.g., app.logger.error(str(e))
    return render_template('find_tasks.html', form=form, tasks=tasks)


@bp.route('/tasks_due_today')
@login_required
def tasks_due_today():
    try:
        today = datetime.today().date()
        tasks = Task.query.filter(
            Task.user_id == current_user.id,
            extract('year', Task.deadline) == today.year,
            extract('month', Task.deadline) == today.month,
            extract('day', Task.deadline) == today.day
        ).all()
        if not tasks:
            flash('No tasks due today.', 'info')
    except SQLAlchemyError as e:
        flash('An error occurred while querying tasks.', 'error')
        # 可以在这里记录日志 e.g., app.logger.error(str(e))
        tasks = []
    return render_template('tasks_due_today.html', tasks=tasks)

def check_status():
    tasks = Task.query.filter_by(user_id=current_user.id, valid=True).all()
    currentDateTime = datetime.now()
    for task in tasks:
        form = TaskForm(obj=task)
        if task.status == 'Completed':
            task.valid = False
            flash('One task has been completed.')
        else:
            if task.deadline < currentDateTime:
                task.status = 'Expired'
            elif task.status == 'Expired':
                task.status = 'Unstarted'
    db.session.commit()