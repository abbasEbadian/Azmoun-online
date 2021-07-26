from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_uploads import configure_uploads, IMAGES, UploadSet
import os
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/db.db"
app.config["APP_NAME"] = "online_test"
app.config["SECRET_KEY"] = "17ab226de066a0f995895791b9e726fbb14042df6583763d1df5084dfc3b53e8"
app.config["UPLOADS_DEFAULT_DEST"] = app.config["APP_NAME"] + '/static'
app.config["UPLOADS_DEFAULT_URL"] = app.config["APP_NAME"] + '/static'

app.config["UPLOADED_PROFILEPICS_DEST"] = app.config["UPLOADS_DEFAULT_DEST"] + '/uploads/profile_pics'
app.config["UPLOADED_QUESTIONPICS_DEST"] = app.config["UPLOADS_DEFAULT_DEST"]+'/uploads/question_pics'
print(app.config["UPLOADED_QUESTIONPICS_DEST"])
app.config["UPLOADS_DEFAULT_URL"] = 'uploads/images'
profile_pics = UploadSet('profilepics', IMAGES)
question_pics = UploadSet('questionpics', IMAGES)
configure_uploads(app, (profile_pics, question_pics))

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message  = "برای دسترسی به این صفحه ابتدا باید وارد شوید."
login_manager.login_message_category   = "info"
from online_test.routes import *
from online_test.models import *
from  . import filter_templates
app.jinja_env.globals['get_question_template'] = get_question_template
if not User.query.all():
    admin = User(name="ادمین", identifier="949621565", user_type="admin", password=bcrypt.generate_password_hash("admin"))
    t1 = User(name="عزیز حنیفی", identifier="111112222", user_type="teacher", password=bcrypt.generate_password_hash("111112222"))
    t2 = User(name="ماهی", identifier="222223333", user_type="teacher", password=bcrypt.generate_password_hash("222223333"))
    s1 = User(name="میلاد درخشی", identifier="555554444", user_type="student", password=bcrypt.generate_password_hash("555554444"))
    s2 = User(name="امیررضا عبادیان", identifier="666667777", user_type="student", password=bcrypt.generate_password_hash("666667777"))
    c1 = Course(name="شبکه کامپیوتری", units=3)
    c2 = Course(name="ساختمان داده", units=3)
    db.session.add_all([admin, t1, t2, s1, s2, c1, c2])
    db.session.commit()

