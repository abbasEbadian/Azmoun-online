from datetime import datetime, time
from online_test import db, login_manager, app
from flask_login import UserMixin
import jdatetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
DATE_FORMAT = "%Y/%m/%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = DATE_FORMAT + " " + TIME_FORMAT

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

enrolls = db.Table('enrolls', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
   db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
)

completed_exams = db.Table('completed_exams',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('exam_id', db.Integer, db.ForeignKey('exam.id'))
)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Full name
    identifier = db.Column(db.String(10), nullable=False, unique=True)
    user_type = db.Column(db.String(30), default='student')
    password = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(50))
    answers = db.relationship("Answer", backref="student")
    courses_of_teacher = db.relationship('Course', backref="teacher")
    courses_of_student = db.relationship('Course', secondary=enrolls, backref=db.backref("enrolled_students", lazy="dynamic"))
    completed_exams = db.relationship('Exam', secondary=completed_exams, backref=db.backref("completed_students", lazy="dynamic"))
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_teacher(self):
        return self.user_type == 'teacher'

    @property
    def is_student(self):
        return self.user_type == 'student'
        
    @property
    def is_admin(self):
        return self.user_type == 'admin' or self.id == 1

    def units_count(self):
        return sum([x.units for x in self.courses_of_student])

    def get_reset_token(self, expire_seconds=1800):
        s = Serializer(app.config['SECRET_KEY'], expire_seconds)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except :
            return None
        return User.query.get(int(user_id))

    def __repr__(self):
        return str(self.id) + ":" + self.name + " " + self.identifier 
    

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    units = db.Column(db.Integer, default=1)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    exams = db.relationship("Exam", backref="course")
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return str(self.id) + ":" + self.name


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    duration = db.Column(db.Integer, default=60)
    questions = db.relationship("Question", backref="exam")
    answers = db.relationship("Answer", backref="exam")
    date = db.Column(db.DateTime)
    points = db.Column(db.Integer)
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def jalali_datetime(self):
        d = jdatetime.datetime.fromgregorian(datetime=self.date)
        d = d.strftime(DATETIME_FORMAT)
        return d

    @property
    def jalali_datetime_o(self):
        d = jdatetime.datetime.fromgregorian(datetime=self.date)
        return d
    
    @property
    def serialize(self):
        return {
            "id": self.id,
            "course_id": self.course.id, 
            "course_name": self.course.name,
            "duration": self.duration,
            "question_ids": [x.id for x in self.questions],
            "date": self.date.timestamp(), 
            "create_date": jdatetime.datetime.fromgregorian(datetime=self.create_date).strftime(DATETIME_FORMAT)
        }
    
    @property
    def unix(self):
        return int(self.date.timestamp())

    def is_expired(self):
        secs = (datetime.fromtimestamp(int(self.unix)) - datetime.now()).total_seconds()
        return secs + (self.duration * 60)<= 0  

    def is_ongoing(self):
        secs = (datetime.fromtimestamp(int(self.unix)) - datetime.now()).total_seconds()
        return  secs < 0 and secs + (self.duration * 60) > 0  
    
    def get_score(self, user):
        ans = list(filter(lambda x: x.student == user, self.answers))
        score = sum([x.is_currect for x in ans]) / (len(ans) or 1)
        return self.points * score

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    answer_1 = db.Column(db.String(200))
    answer_2 = db.Column(db.String(200))
    answer_3 = db.Column(db.String(200))
    answer_4 = db.Column(db.String(200))
    currect_answer = db.Column(db.Integer)
    image = db.Column(db.String(100))
    answers = db.relationship("Answer", backref="question")
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    create_date = db.Column(db.DateTime, default=datetime.utcnow)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_currect(self):
        q = self.question
        return self.value == q.currect_answer