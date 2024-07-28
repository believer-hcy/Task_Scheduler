from flask import render_template, flash, redirect, url_for, request 
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Task
from app.forms import LoginForm, RegistrationForm, TaskForm, DateForm
from flask import Blueprint
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    #for task in tasks:
    #   print(task.title , task.description)
    currentDateTime = datetime.now()
    for task in tasks:
        if task.status != 'Completed':
            if task.deadline < currentDateTime:
                task.status = 'Expired'
        
    return render_template('index.html', title='Home', tasks=tasks)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
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

@bp.route('/history', methods=['GET'])
def history():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    #for task in tasks:
    #   print(task.title , task.description)
    currentDateTime = datetime.now()
    for task in tasks:
        if task.deadline < currentDateTime:
            task.status = 'Expired'

    return render_template('history.html', tasks=tasks)

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
    return render_template('register.html', title='Register', form=form)

from sqlalchemy.exc import SQLAlchemyError  # 导入 SQLAlchemy 的异常类
# routes.py (inside a blueprint folder, e.g., main)
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)
@bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        try:
            title = form.title.data
            description = form.description.data
            deadline = form.deadline.data
            importance = form.importance.data
            status = form.status.data

            new_task = Task(user_id=current_user.id, title=title, description=description, deadline=deadline, importance=importance, status=status)
            
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('main.index'))
        except SQLAlchemyError as e:
            db.session.rollback()  # 回滚数据库会话
            flash('An error occurred while adding the task.', 'error')
            # 可以在这里记录日志 e.g., app.logger.error(str(e))
    return render_template('add_task.html', form=form)

@bp.route('/edit_task<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    form = TaskForm()
    if form.validate_on_submit():
        try:
            task.title = form.title.data
            task.description = form.description.data
            task.deadline = form.deadline.data
            task.importance = form.importance.data
            task.status = form.status.data

            # new_task = Task(user_id=current_user.id, title=title, description=description, deadline=deadline, importance=importance, status=status)
            
            # db.session.add(task)
            db.session.commit()
            flash('Task changed successfully!', 'success')
            return redirect(url_for('main.index'))
        except SQLAlchemyError as e:
            db.session.rollback()  # 回滚数据库会话
            flash('An error occurred while adding the task.', 'error')
            # 可以在这里记录日志 e.g., app.logger.error(str(e))
    return render_template('edit_task.html', form=form, task=task)
    # return redirect(url_for('main.edit_task', id=task.id))

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
    return redirect(url_for('main.index'))

from sqlalchemy import extract

@bp.route('/completed/<int:id>')
@login_required
def completed(id):
    task = Task.query.get_or_404(id)
    task.status = 'Completed'
    db.session.commit()
    flash('One task has been completed.')
    return redirect(url_for('main.index'))

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