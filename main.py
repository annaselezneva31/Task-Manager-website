from dataclasses import dataclass
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from wtforms import StringField, SubmitField, URLField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, URL
from sqlalchemy import Integer, String, DateTime
from datetime import datetime
import os

app =Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("APP_SECRET_KEY")
API_KEY = os.environ.get("API_KEY")
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

def strtobool(val):
    if val is not None:
        val = val.lower()
        if val in ('y', 'yes', 't', 'true', 'on', '1'):
            return 1
        elif val in ('n', 'no', 'f', 'false', 'off', '0'):
            return 0
        else:
            raise ValueError("invalid truth value %r" % (val,))
    else:
        return 0

# Cafe TABLE Configuration
@dataclass
class Tasks(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(String(500), nullable=False)
    date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_done: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    tag: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str] = mapped_column(String(500), nullable=True)

with app.app_context():
    # db.create_all()
    RESULT = db.session.execute(db.select(Tasks))
    ALL_TASKS = RESULT.scalars().all()
    ALL_AUTHORS = set(task.author for task in ALL_TASKS)
    ALL_AUTHORS.add("Select")
    ALL_TAGS = set(task.tag for task in ALL_TASKS)
    ALL_TAGS.add("Select")
    ALL_STATUS = set(task.status for task in ALL_TASKS)
    ALL_STATUS.add("Select")


# Cafe Adding Form
class AddTask(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    date_deadline = DateField('Deadline date', validators=[DataRequired()])
    time_deadline =  TimeField('Deadline time', validators=[DataRequired()])
    description = StringField('Task Description', validators=[DataRequired()])
    tag = SelectField('Tag', choices=[("Work", "Work"),
                                                  ("Household", "Household"),
                                                  ("Hobby", "Hobby"), ], validators=[DataRequired()])
    status = SelectField('Status', choices=[("To Do", "To Do"),
                                                     ("In Progress", "In Progress"),
                                                     ("Done", "Done"),
                                                     ("Canceled", "Canceled"),
                                                     ("Backlog", "Backlog"), ], validators=[DataRequired()])
    link = URLField(label='Link', validators=[URL()])
    submit = SubmitField('Add Task')

class UpdateTask(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    date_deadline = DateField('Deadline date', validators=[DataRequired()])
    time_deadline =  TimeField('Deadline time', validators=[DataRequired()])
    description = StringField('Task Description', validators=[DataRequired()])
    tag = SelectField('Tag', choices=[("Work", "Work"),
                                                  ("Household", "Household"),
                                                  ("Hobby", "Hobby"), ], validators=[DataRequired()])
    status = SelectField('Status', choices=[("To Do", "To Do"),
                                                     ("In Progress", "In Progress"),
                                                     ("Done", "Done"),
                                                     ("Canceled", "Canceled"),
                                                     ("Backlog", "Backlog"), ], validators=[DataRequired()])
    link = URLField(label='Link', validators=[URL()])
    submit = SubmitField('Update Task')

class SearchForm(FlaskForm):
    task_name = StringField('Task Name')
    author = SelectField('Author', choices=ALL_AUTHORS, default="Select")
    date_deadline = DateField('Deadline date')
    tag = SelectField('Tag', choices=ALL_TAGS, default="Select")
    status = SelectField('Status', choices=ALL_STATUS, default="Select")
    search = SubmitField('Search')




@app.route("/", methods=["GET", "POST", "PATCH"])
def home():
    form = AddTask()
    update_form = UpdateTask()
    search_form = SearchForm()
    result = db.session.execute(db.select(Tasks))
    all_tasks = result.scalars().all()
    now = datetime.today()
    return render_template("index.html", form=form, update_form=update_form, tasks=all_tasks, now=now, search_form=search_form)

@app.route("/add", methods=["GET", "POST"])
def add_task():
    now = datetime.today()
    new_task = Tasks(
        task_name=request.form.get("task_name"),
        author=request.form.get("author"),
        date_created=now,
        date_deadline=datetime.strptime(f"{request.form.get('date_deadline')} {request.form.get('time_deadline')}",
                                        '%Y-%m-%d %H:%M'),
        description=request.form.get("description"),
        tag=request.form.get("tag"),
        status=request.form.get("status"),
        link=request.form.get("link"),
    )
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/update/<task_id>", methods=["GET", "PATCH"])
def update_task(task_id):
    task_by_id = db.session.get(Tasks, task_id)
    if request.form.get("task_name"):
        task_by_id.task_name = request.form.get("task_name")
        task_by_id.author = request.form.get("author")
        task_by_id.date_deadline = datetime.strptime(f"{request.form.get('date_deadline')} {request.form.get('time_deadline')}", '%Y-%m-%d %H:%M:%S')
        task_by_id.description = request.form.get("description")
        task_by_id.tag = request.form.get("tag")
        task_by_id.status = request.form.get("status")
        task_by_id.link = request.form.get("link")
    else:
        task_by_id.status = request.args.get("new_status")

    db.session.commit()
    return redirect(url_for('home'))


@app.route("/search", methods=["GET", "POST"])
def search_tasks():
    form = AddTask()
    update_form = UpdateTask()
    result = db.session.execute(db.select(Tasks))
    tasks_by_filter = result.scalars().all()
    now = datetime.today()

    task_name = request.form.get("task_name")
    author = request.form.get("author")
    tag = request.form.get("tag")
    status = request.form.get("status")
    if task_name and task_name is not None:
        tasks_by_filter = [task for task in tasks_by_filter if task.task_name == task_name]
    if author != "Select" and author is not None:
        tasks_by_filter = [task for task in tasks_by_filter if task.author == author]
    if request.form.get('date_deadline'):
        date_deadline = datetime.strptime(f"{request.form.get('date_deadline')}", '%Y-%m-%d')
        tasks_by_filter = [task for task in tasks_by_filter if date_deadline < task.date_deadline]
    if tag != "Select" and not request.args.get("tag"):
        tasks_by_filter = [task for task in tasks_by_filter if task.tag == tag]
    if status != "Select" and status is not None:
        tasks_by_filter = [task for task in tasks_by_filter if task.status == status]

    if request.args.get("tag"):
        tasks_by_filter = [task for task in tasks_by_filter if task.tag == request.args.get("tag")]
    search_form = SearchForm(
        task_name=task_name,
        author=author,
        tag=tag,
        status=status,
    )
    return render_template("index.html", form=form, tasks=tasks_by_filter, now=now, search_form=search_form, update_form=update_form)

@app.route("/delete/<task_id>", methods=["GET", "DELETE"])
def delete_task(task_id):
    task_by_id = db.session.get(Tasks, task_id)
    if task_by_id is not None:
        db.session.delete(task_by_id)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a task with that id."}), 404

@app.route("/test")
def test():
    return render_template("test.html")

if __name__ == '__main__':
    app.run(debug=True, port=8000)
