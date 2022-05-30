from flask import Flask, render_template, url_for, redirect, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, UserMixin, LoginManager, current_user, logout_user
from functools import wraps


app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
database = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_admin(admin_id):
    return Admin.query.get(admin_id)


class CreateStoryForm(FlaskForm):
    title = StringField('TITLE', validators=[DataRequired()])
    stardate = StringField('STARDATE', validators=[DataRequired()])
    author = StringField('AUTHOR', validators=[DataRequired()])
    story = CKEditorField('THE STORY', validators=[DataRequired()])
    submit = SubmitField('Post Story')


class LoginForm(FlaskForm):
    email = StringField('ADMIRAL', validators=[DataRequired()])
    password = PasswordField('PASSWORD', validators=[DataRequired()])
    submit = SubmitField('LOG IN')


# noinspection PyUnresolvedReferences
class Admin(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True)
    email = database.Column(database.String(100), unique=True)
    password = database.Column(database.String(70))
    __tablename__ = 'Admin'


# noinspection PyUnresolvedReferences
class Storys(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    title = database.Column(database.String(70), unique=True, nullable=False)
    stardate = database.Column(database.String(70), unique=True, nullable=False)
    author = database.Column(database.String(70), nullable=False)
    story = database.Column(database.Text, nullable=False)
    __tablename__ = 'Storys'

#database.create_all()


@app.route('/')
def all_storys():
    allstorys = Storys.query.all()
    return render_template('index.html', allstorys=allstorys)


@app.route('/story', methods=['Get', 'Post'])
def write_new_story():
    allstorys = Storys.query.all()
    form = CreateStoryForm()
    if form.validate_on_submit():
        new_story = Storys(title=form.title.data,
                           stardate=form.stardate.data,
                           author=form.author.data,
                           story=form.story.data,
                           )
        database.session.add(new_story)
        database.session.commit()
        return redirect(url_for('all_storys'))
    return render_template('story.html', form=form, allstorys=allstorys)


def admin_only(e):
    @wraps(e)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return e(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['Get','Post'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            flash('Sorry Admiral this is not your Login!')
            return redirect(url_for('login'))
        elif password != admin.password:
            flash('Sorry Admiral this is not you Password!')
            return redirect(url_for('login'))
        else:
            login_user(admin)
            return redirect(url_for('all_storys'))


    return render_template('login.html', form=form,  current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('all_storys'))


@app.route('/reading/<int:index>', methods=['GET'])
def reading_story(index):
    allstorys = Storys.query.all()
    requested_story = Storys.query.get(index)
    return render_template('reading.html', story=requested_story, allstorys=allstorys)


@app.route('/delete/<story_id>')
@admin_only
def delete_story(story_id):
    requested_story = Storys.query.get(story_id)
    database.session.delete(requested_story)
    database.session.commit()
    return redirect(url_for('all_storys'))


@app.route('/edit-story/<int:story_id>', methods=['Get', 'Post'])
def editing_story(story_id):
    story = Storys.query.get(story_id)
    edit_form = CreateStoryForm(
        title=story.title,
        stardate=story.stardate,
        author=story.author,
        story=story.story,
    )
    if edit_form.validate_on_submit():
        story.title = edit_form.title.data
        story.stardate = edit_form.stardate.data
        story.author = edit_form.author.data
        story.story = edit_form.story.data
        database.session.commit()
        return redirect(url_for('reading_story', index=story.id))
    return render_template('story.html', form=edit_form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
