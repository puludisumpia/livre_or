from datetime import datetime
import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_security import Security, UserMixin, RoleMixin, SQLAlchemyUserDatastore, \
    LoginForm, current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_babelex import Babel

app = Flask(
    __name__,
    template_folder="assets/templates",
    static_folder="assets/static"
)
app.config["SECRET_KEY"] = "^pùmolghjklm^$^lk"

app.config["BABEL_DEFAULT_LOCALE"] = "fr"

app.config["SECURITY_PASSWORD_HASH"] = "sha256_crypt"
app.config["SECURITY_PASSWORD_SALT"] = "pomlkhjgfhjolikjhgfdgh"

if os.environ.get("DATABASE_URL") is None:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///assets/data.db"
else:
     app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

bootstrap = Bootstrap(app)
babel = Babel(app)

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'))
)

class Role(db.Model, RoleMixin):
    __tablename__ = "roles"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.username

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    corps = db.Column(db.Text(), nullable=False)
    date = db.Column(db.DateTime(), default=datetime.utcnow())

    def __str__(self):
        return self.name


class ExtendLoginForm(LoginForm):
    email = EmailField(label="Identifiant")
    password = PasswordField(label="Mot de passe")
    remember = BooleanField(label="Se souvenir de mon identifiant")
    submit = SubmitField(label="Connexion")

class MessageForm(FlaskForm):
    name = StringField(label="Votre nom", validators=[DataRequired()])
    corps = TextAreaField(label="Votre message", validators=[DataRequired()])
    submit = SubmitField(label="Poster")


class HomeAdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role("admin")

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("security.login", next=request.url))

class MessageAdminView(ModelView):
    pass

class UserAdminView(ModelView):
    pass

class RoleAdminView(ModelView):
    pass

@app.route("/", methods=["GET", "POST"])
def index():
    form = MessageForm()
    if request.method == "POST":
        name = form.name.data
        corps = form.corps.data

        new_message = Message(
            name=name,
            corps=corps
        )

        db.session.add(new_message)
        db.session.commit()

        flash("Message posté avec succès", "success")
        return redirect(url_for("index"))
    else:
        form = MessageForm()

    posts = db.session.query(Message).order_by(Message.date.desc())

    page = request.args.get("page")

    if page and page.isdigit():
        page = int(page)
    else:
        page = 1
    pages = posts.paginate(page=page, per_page=10)
    return render_template(
        "index.html", 
        form=form, 
        posts=posts,
        pages=pages
    )

# Flask-Security 
user_store = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_store, login_form=ExtendLoginForm)

# Flask-Admin
admin = Admin(
    app, 
    name="LIVRE D'OR",
    template_mode="bootstrap4", 
    url="/",
    index_view=HomeAdminView(name="Gestion")
)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    db.create_all()
    admin.add_view(MessageAdminView(Message, db.session))
    admin.add_view(UserAdminView(User, db.session))
    admin.add_view(RoleAdminView(Role, db.session))
    app.run(debug=False)
 