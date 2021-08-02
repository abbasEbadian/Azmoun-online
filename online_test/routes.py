from wtforms.form import FormMeta
from online_test import app
from flask import render_template, request, flash, redirect, url_for, jsonify, g
import json, os
from online_test.models import User, Course, Exam, Question, Answer
from online_test.forms import (RegisterForm, LoginForm, QuestionForm, ExamForm,
                                EmailResetRequestForm, ResetPasswordForm)
from sqlalchemy import desc, or_
from online_test import db, app, bcrypt, profile_pics, question_pics, mail
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from datetime import date as ddate
from flask_mail import Message
@app.route("/")
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for(login))
    return redirect(url_for(current_user.user_type))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden403(e):
    return render_template('403.html'), 403


@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for(current_user.user_type))
    data = {
        "students":  User.query.filter_by(user_type="student").all(),
        "teachers":  User.query.filter_by(user_type="teacher").all(),
        "courses":  Course.query.all()
    }
    data["student_counts"] =  { teacher.id: sum([len(c.enrolled_students.all()) for c in teacher.courses_of_teacher]) for teacher in data['teachers'] }
    data["student_units"] =  { student.id: sum([c.units for c in student.courses_of_student]) for student in data['students'] }

    return render_template('admin.html', **data)

@app.route('/teacher/<menu_name>/<param1>')
@app.route('/teacher/<menu_name>')
@app.route('/teacher')
@login_required
def teacher(menu_name=None, param1=None): 
    if not menu_name: return redirect('/teacher/exams')
    teacher_template_path = os.path.join(app.instance_path.replace('instance', app.config['APP_NAME']), 'templates', 'teacher')
    if not os.path.isfile(os.path.join(teacher_template_path, menu_name+'.html')):
        return page_not_found(404)
    if not current_user.is_teacher: 
        return forbidden403(403)
    
    data = {
        "body_class" : "login_page",
        "courses": Course.query.filter_by(teacher=None),
        "exam_form": ExamForm(),
        "param1": param1
    }
    exams = []
    for c in current_user.courses_of_teacher:
        exams += c.exams
    data["exams"] = exams
    
    if param1:
        editable_exam = Exam.query.get(param1)
        if editable_exam:
            data["the_exam"] = editable_exam
            if editable_exam.course.teacher.id != current_user.id:
                return forbidden403(403)
    return render_template(f"/teacher/{menu_name}.html", **data)


@app.route('/student/<menu_name>/<param1>')
@app.route('/student/<menu_name>')
@app.route('/student/')
@login_required
def student(menu_name=None, param1=None):
    if not menu_name: return redirect('/student/exams')
    student_template_path = os.path.join(app.instance_path.replace('instance', app.config['APP_NAME']), 'templates', 'student')
    if not os.path.isfile(os.path.join(student_template_path, menu_name+'.html')):
        return page_not_found(404)
    if not current_user.is_student: 
        return forbidden403(403)
    data = {
        "courses": Course.query.filter(Course.id not in [x.id for x in current_user.courses_of_student]).all(),
    }
    exams = []
    for c in current_user.courses_of_student:
        exams += c.exams
    data["exams"] = exams
    # if param1:
    #     editable_exam = Exam.query.get(param1)
    #     data["the_exam"] = editable_exam
    #     if editable_exam.course.teacher.id != current_user.id:
    #         return forbidden403(403)
    return render_template(f"/student/{menu_name}.html", **data)


@app.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.user_type))
    form = RegisterForm()
    if form.validate_on_submit():
        last_id = User.query.first() 
        hash_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = {
            "name": form.name.data,
            "identifier": form.identifier.data,
            "password": hash_pwd,
            "email": form.email.data,
            "user_type": not last_id and 'admin' or  form.is_teacher.data and 'teacher' or 'student' 
        }
        user = User(**new_user)
        db.session.add(user)
        db.session.commit()
        flash("حساب کاربری با موفقیت ایجاد شد.", 'success')
        return redirect(url_for('login'))
    data = {
        "body_class" : "gray_bg"
    }
    return render_template('register.html', form=form, **data)
        

@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.user_type))

    form = LoginForm()
    user = User.query.filter(or_(User.identifier==form.identifier.data,User.email==form.identifier.data)).first()
    if form.validate_on_submit():
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for(user.user_type))
        else:
            flash("شماره دانشجویی یا رمز عبور اشتباه است", 'danger')

    data = {
        "body_class" : "gray_bg"
    }
    return render_template('login.html', form=form, **data)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect( url_for("login") )


@app.route('/get_question_template/<question_number>/exam_<exam_id>/')
@app.route('/get_question_template/<question_number>/question_<question_id>/')
def get_question_template(question_number=None, exam_id=None, question_id=None, request_type="from_js"):
    form = QuestionForm()
    if question_id:
        q = Question.query.get(question_id)  
        data = {
            "qform":form,
            "exam_id": q.exam.id,
            "question_number":question_number, 
            "question_id":q.id, 
            "question": q,
        }
    elif exam_id:
        data = {
            "qform":form,
            "exam_id": exam_id,
            "question_number":question_number, 
        }
    if request_type == "from_js":
        return jsonify({"body": render_template("question.html", **data)})
    else:
        return render_template("question.html", **data)



@app.route('/new_teacher' , methods=["POST", "GET"])
def new_teacher():
    name = request.json.get("name")
    code = request.json.get("code")
    teacher = User.query.filter_by(identifier=code).first()
    if not teacher:
        teacher = User.query.filter_by(name=name, user_type="teacher").first()
    if teacher:
        return jsonify({"result": "error", "cause":"با این مشخصات قبلا  کاربر ثبت شده است."})

    hash_pwd = bcrypt.generate_password_hash(code).decode('utf-8')
    teacher = User(name=name, identifier=code, user_type="teacher", password=hash_pwd)
    db.session.add(teacher)
    db.session.commit()
    return jsonify({"result": "success"})



@app.route('/new_student' , methods=["POST", "GET"])
def new_student():
    name = request.json.get("name")
    code = request.json.get("code")
    student = User.query.filter_by(identifier=code).first()
    if not student:
        student = User.query.filter_by(name=name, user_type="student").first()
    if student:
        return jsonify({"result": "error", "cause":"با این مشخصات قبلا  کاربر ثبت شده است."})

    hash_pwd = bcrypt.generate_password_hash(code).decode('utf-8')
    student = User(name=name, identifier=code, user_type="student", password=hash_pwd)
    db.session.add(student)
    db.session.commit()
    return jsonify({"result": "success"})


@app.route('/new_course' , methods=["POST", "GET"])
def new_course():
    name = request.json.get("name")
    units = request.json.get("code")
    course = Course.query.filter_by(name=name).first()
    if course:
        return jsonify({"result": "error", "cause":"این درس قبلا ثبت شده است."})
    course = Course(name=name,  units=units)
    db.session.add(course)
    db.session.commit()
    return jsonify({"result": "success"})


@app.route('/add_course_to_user/<course_id>', methods=["POST", "GET"])
def add_course_to_user(course_id):
    course = Course.query.get(int(course_id))
    if course in current_user.courses_of_student:
        return jsonify({"result": "fail", "cause": "این درس قبلا انتخاب شده است."})

    if current_user.is_teacher:
        current_user.courses_of_teacher.append(course)
    elif current_user.is_student:
        units_count = current_user.units_count()
        if course.units + units_count > 18:
            return jsonify({"result": "fail", "cause": "تعداد واحد ها نمی تواند بیشتر از 18 باشد."})
       
        current_user.courses_of_student.append(course)

    db.session.commit()
    return jsonify({"result": "success"})

@app.route("/create_new_exam", methods=["POST", "GET"])
def create_new_exam():
    title = request.form.get("title")
    unix = request.form.get("date_unix")
    course = request.form.get("course")
    duration = request.form.get("duration")
    points = request.form.get("points")
    date = datetime.fromtimestamp(int(unix)//1000)
    course = Course.query.get(int(course))
    similar_date_exams = Exam.query.filter_by(date=date, course_id=course.id).all()
    if similar_date_exams:
        return jsonify({"result": "fail", "cause": "برای این درس در این تاریخ آزمون ثبت شده است."})
        
    exam = Exam(name=title, duration=duration, date=date, course=course, points=points)
    db.session.commit()
    return jsonify({"result": "success", "exam_id": exam.id})

@app.route("/update_exam/<exam_id>", methods=["POST", "GET"])
def update_exam(exam_id):
    exam = Exam.query.filter_by(id=int(exam_id))
    course = request.form.get("course")
    course1 = Course.query.get(int(course))
    unix = request.form.get("date_unix", 0)
    data = {
        "name":  request.form.get("title"),
        "duration":  request.form.get("duration"),
        "course_id": course1.id
    }
    if unix:
        data["date"] = datetime.fromtimestamp(int(unix)//1000)
    exam.update(data)
    db.session.commit()
    return jsonify({"result": "success", "exam_id": exam.first().id})


@app.route('/save_question/<exam_id>/<question_id>', methods=["POST", "GET"])
@app.route('/save_question/<exam_id>', methods=["POST", "GET"])
def save_question(exam_id, question_id=-1):
    exam = Exam.query.get(int(exam_id))
    update_kw = [
        Question.text,
        Question.answer_1,
        Question.answer_2,
        Question.answer_3,
        Question.answer_4,
        Question.currect_answer
    ]
    data = {
        "text" : request.form.get("question_text"),
        "answer_1" : request.form.get("answer_1").strip(),
        "answer_2" : request.form.get("answer_2").strip(),
        "answer_3" : request.form.get("answer_3").strip(),
        "answer_4" : request.form.get("answer_4").strip(),
        "currect_answer" : int(request.form.get("currect_answer")),
    }
    if len(set([data["answer_1"], data["answer_2"], data["answer_3"], data["answer_4"]])) != 4:
        return jsonify({"result": "fail", "cause": "گزینه ها نمی توانند تکراری باشند"})
    q = Question.query.filter_by(id=question_id)
    if q.all():
        q.update({k: v for k,v in zip(update_kw, data.values())})
        q = q.first()
    else:
        q = Question(**data)
        db.session.add(q)
    q.exam = exam
    image = request.files['image']
    if image.filename and q:
        image.filename = str(q.id) + "_" + image.filename
        for ext in ['.png', '.jpg']:
            p = os.path.join(os.getcwd() , app.config.get("UPLOADED_QUESTIONPICS_DEST"), str(q.id)+ext) 
            if os.path.isfile(p):
                os.remove(p)
        question_pics.save(image)
        q.image = "uploads/question_pics/"+image.filename
    db.session.commit()
    return jsonify({"result": "success", "q": str(q)})
    

@app.route('/get_exam/<exam_id>')
def get_exam_info_for_edit(exam_id):
    exam = Exam.query.get(int(exam_id))
    return jsonify({"result": "success", "exam": exam.serialize})


@app.route("/question/delete/<question_id>", methods=["POST", "GET"])
def delete_question(question_id):
    q = Question.query.get(int(question_id))
    if not q:
        return jsonify({"result": "fail", "cause": "این سوال یافت نشد."})
    for ext in ['.png', '.jpg']:
        p = os.path.join(os.getcwd() , app.config.get("UPLOADED_QUESTIONPICS_DEST"), str(q.id)+ext) 
        if os.path.isfile(p):
            os.remove(p)

    db.session.delete(q)
    db.session.commit()
    return jsonify({"result": "success"})

@app.route("/exam/delete/<exam_id>", methods=["POST", "GET"])
def delete_exam(exam_id):
    q = Exam.query.get(int(exam_id))
    if not q:
        return jsonify({"result": "fail", "cause": "این آزمون یافت نشد."})
    for qu in q.questions:
        delete_question(qu.id)
    db.session.delete(q)
    db.session.commit()
    return jsonify({"result": "success"})

@app.route("/exam/<exam_id>")
@login_required
def exam(exam_id):
    exam = Exam.query.get(int(exam_id))      
    if exam and exam.course not in current_user.courses_of_student:
        return redirect(url_for('student'))  
    if exam and exam in current_user.completed_exams:
        return redirect(url_for('exam_result', exam_id=exam_id))
    if exam and exam.is_ongoing():
        get_source()
        return redirect(url_for('exam_q', exam_id=exam.id, question_index=1))
    return render_template('exam.html', exam=exam)

@app.teardown_appcontext
def teardown_source(exception):
   return g.pop('source', None)


def get_source():
    if 'source' not in g:
        g.source = 'main'
    return g.source


@app.route("/exam/<exam_id>/question/<question_index>")
@login_required
def exam_q(exam_id, question_index):
    if not get_source():
        return redirect(url_for('exam', exam_id=exam_id))

    question_index = int(question_index)
    exam = Exam.query.get(int(exam_id))
    question = None
    def red(q):
        return redirect(url_for('exam_q', exam_id=exam_id, question_index=q))
    if question_index < 1 :
        return red(1)
    elif question_index > len(exam.questions):
        return red(len(exam.questions))
    else:
        question = exam.questions[question_index-1]
    data = dict(exam=exam, question=question, question_index=question_index)
    answers = {idx : Answer.query.filter_by(student=current_user, question=q).first() for idx,q in enumerate(exam.questions)}
    data["answers"] = answers
    if answers[question_index-1]:
        data["answer"] = answers[question_index-1].value
    return render_template('exam_main.html', **data)


@app.route('/submit_answer/<question_id>/<answer>', methods=["GET", "POST"])
@login_required
def submit_answer(question_id, answer):
    question = Question.query.get(int(question_id))
    exam = question.exam
    if exam in current_user.completed_exams:
        return jsonify({"result": "fail", "redirect": f"/exam_result/{exam.id}"})
    ans = Answer.query.filter(Answer.student==current_user, Answer.exam==exam, Answer.question==question).first()
    if not ans:
        ans = Answer(student=current_user, exam=exam, question=question, value=int(answer))
        db.session.add(ans)
    db.session.commit()

    return jsonify({"result": "success", "msg": "با موفقیت ثبت شد."})


@app.route('/complete_exam/<exam_id>')
@login_required
def complete_exam(exam_id):
    exam = Exam.query.get(int(exam_id))
    if exam not in current_user.completed_exams:
        current_user.completed_exams.append(exam)
        db.session.commit()
    return jsonify({"result": "success"})


@app.route('/exam_result/<exam_id>')
@login_required
def exam_result(exam_id):
    exam = db.session.query(Exam).get(int(exam_id))
    if not exam or  exam not in current_user.completed_exams or exam.date > datetime.now():
        return redirect(url_for('exam', exam_id=exam_id))
    ans = list(filter(lambda x: x.exam.id == int(exam_id) , current_user.answers))
    currect = sum([a.is_currect for a in ans])
    total = len(exam.questions)
    point = exam.get_score(current_user)

    return render_template("exam_result.html", point=point, exam=exam, currect=currect, total=total)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message("لینک بازنشانی رمز عبور", sender=app.config['MAIL_SENDER'], recipients=[user.email])
    msg.body = f'''
برای بازنشانی رمز عبور خود به لینک زیر مراجعه کنید:
{url_for('reset_password', token=token, _external=True) }
    '''
    mail.send(msg)
    print("sent")

@app.route("/reset_password_request", methods=["POST", "GET"])
def reset_password_request():
    form = EmailResetRequestForm()
    print("CAME 1", form.validate_on_submit())
    print(form.errors)
    if form.validate_on_submit():
        print("CAME")
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("لینک بازنشانی رمز عبور به ایمیل شما ارسال شد.", 'info')
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html', form=form)

@app.route("/reset_password/<token>", methods=["POST", "GET"])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash("کلید نامعتبر است یا منقضی شده است.", 'warning')
        return redirect(url_for('reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hash_pwd = bcrypt.generate_password_hash(form.password1.data)
        user. password = hash_pwd
        db.session.commit()
        flash("رمز شما با موفقی تغییر یافت.", 'success')
        return redirect(url_for("login"))
    return render_template('reset_password.html', form=form)
