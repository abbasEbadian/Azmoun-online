from flask_wtf import FlaskForm
from wtforms import  StringField, PasswordField, SubmitField, BooleanField,IntegerField, TextAreaField
from wtforms import  SelectField, HiddenField, DateTimeField
from flask_wtf.file import FileField
from wtforms.fields.html5 import TelField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, length, EqualTo, ValidationError
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
    phone = TelField('شماره همراه',
        validators=[DataRequired(message=empty_message), length(min=11, max=11, message=length_message.format(11))],
        render_kw={"placeholder": "09..."})
    password = PasswordField('رمز عبور', validators=[DataRequired(message=empty_message)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(message=empty_message), EqualTo('password', message=match_message)])
    is_teacher = BooleanField('ثبت نام به عنوان استاد')
    submit = SubmitField('ثبت نام')

    def validate_identifier(self, identifier):
        user = User.query.filter_by(identifier=identifier.data).first()
        if user:
            raise ValidationError("این نام کاربری قبلا ثبت شده است.")
        
    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError("این شماره همراه قبلا ثبت شده است.")
        

class LoginForm(FlaskForm):
    identifier = StringField('شماره دانشجویی یا همراه', validators=[DataRequired(message=empty_message), length(min=5, max=20, message=length_message.format(5))])
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
    datetime = DateTimeField("تاریخ برگزاری", render_kw={"autocomplete": "off"})
    duration = IntegerField("مهلت آزمون ( دقیقه )", render_kw={"autocomplete": "off"})
    date_unix = HiddenField("", id="date_unix",validators=[DataRequired(message='تاریخ پایان نمیتواند خالی باشد.')])

    