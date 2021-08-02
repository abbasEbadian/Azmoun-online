from flask_wtf import FlaskForm
from wtforms import  StringField, PasswordField, SubmitField, BooleanField,IntegerField, TextAreaField
from wtforms import  SelectField, HiddenField, DateTimeField
from flask_wtf.file import FileField
from wtforms.fields.html5 import TelField, EmailField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, length, EqualTo, ValidationError, Email
from online_test.models import User, Course
from flask_login import current_user

length_message = "حداقل {} کاراکتر"
empty_message = "نمی تواند خالی باشد"
match_message = "رمز عبور های وارد شده یکسان نیستند"
class RegisterForm(FlaskForm):
    name = StringField('نام و نام خانوادگی', validators=[DataRequired(message=empty_message), length(min=5, max=100, message=length_message.format(5))])
    identifier = StringField('شماره دانشجویی',
        validators=[DataRequired(message=empty_message),length(min=9, max=100, message=length_message.format(9))],
        render_kw={"placeholder": "ده رقمی"})
    email = TelField('ایمیل',
        validators=[DataRequired(message=empty_message), length(min=10, max=100, message=length_message.format(10)), Email()],
        render_kw={"placeholder": "example@domain.com"})
    password = PasswordField('رمز عبور', validators=[DataRequired(message=empty_message)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(message=empty_message), EqualTo('password', message=match_message)])
    is_teacher = BooleanField('ثبت نام به عنوان استاد')
    submit = SubmitField('ثبت نام')

    def validate_identifier(self, identifier):
        user = User.query.filter_by(identifier=identifier.data).first()
        if user:
            raise ValidationError("این نام کاربری قبلا ثبت شده است.")
        
    def validate_phone(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("این شماره همراه قبلا ثبت شده است.")
        

class LoginForm(FlaskForm):
    identifier = StringField('شماره دانشجویی یا ایمیل', validators=[DataRequired(message=empty_message), length(min=5, max=20, message=length_message.format(5))])
    password = PasswordField('رمز عبور', validators=[DataRequired(message=empty_message)])
    remember = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود به سایت')


class QuestionForm(FlaskForm):
    question_text = TextAreaField('متن سوال', validators=[DataRequired(message=empty_message)])
    image = FileField("تصویر")
    answer_1 = StringField('گزینه 1', validators=[DataRequired(message=empty_message)], render_kw={"placeholder": "گزینه یک", "autocomplete": "off"})
    answer_2 = StringField('گزینه 2', validators=[DataRequired(message=empty_message)], render_kw={"placeholder": "گزینه دو", "autocomplete": "off"})
    answer_3 = StringField('گزینه 3', validators=[DataRequired(message=empty_message)], render_kw={"placeholder": "گزینه سه", "autocomplete": "off"})
    answer_4 = StringField('گزینه 4', validators=[DataRequired(message=empty_message)], render_kw={"placeholder": "گزینه چهار", "autocomplete": "off"})
    currect_answer = SelectField('گزینه صحیح', choices=[(1, "گزینه 1"), (2, "گزینه 2"), (3, "گزینه 3"), (4, "گزینه 4")])
def get_courses():
    return Course.query.filter_by(teacher=current_user).all()

class ExamForm(FlaskForm):
    title = StringField('عنوان آزمون',  render_kw={"placeholder": "آزمون میانترم ساختمان داده", "autocomplete": "off"})
    course = QuerySelectField('درس مربوطه', query_factory=get_courses,
                                get_pk=lambda a: a.id,
                                get_label=lambda a: a.name)
    datetime = StringField("تاریخ برگزاری", render_kw={"autocomplete": "off"})
    duration = IntegerField("مهلت آزمون ( دقیقه )", render_kw={"autocomplete": "off"})
    date_unix = HiddenField("", id="date_unix",validators=[DataRequired(message='تاریخ پایان نمیتواند خالی باشد.')])
    points = IntegerField('نمره از:', validators=[DataRequired(message=empty_message)], render_kw={"placeholder": "8", "autocomplete": "off"})

    
class ResetPasswordForm(FlaskForm):
    password1 = PasswordField('رمز عبور جدید', validators=[DataRequired(message=empty_message)])
    password2 = PasswordField('تکرار رمز عبور', validators=[DataRequired(message=empty_message)])
    submit=  SubmitField('ثبت رمز جدید')

    def validate_password2(form, password2):
        if form.password1.data != form.password2.data:
            raise ValidationError('رمز های وارد شده یکسان نیستند.')

class EmailResetRequestForm(FlaskForm):
    email = EmailField('ایمیل',
    validators=[DataRequired(message=empty_message), length(min=10, max=100, message=length_message.format(10))],
    render_kw={"placeholder": "example@domain.com"})
    submit = SubmitField('تایید')

    def validate_email(form, email):
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            raise ValidationError("ایمیل وارد شده صحیح نمی باشد.")
