import os  # For working with environment variables and file paths
from flask import Flask, render_template, url_for, redirect, request, flash, session  # Core Flask features
from werkzeug.security import generate_password_hash, check_password_hash  # For secure password handling
from flask_sqlalchemy import SQLAlchemy  # For database integration
from flask_migrate import Migrate  # For handling database migrations
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Use an environment variable for production

# Database URI (SQLite in this case)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///QuizMaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define models

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Optional
    chapters = db.relationship('Chapter', backref='subject', lazy=True)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Optional
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete='CASCADE'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=True)  # Optional
    time_duration = db.Column(db.String(5), nullable=True)  # Format HH:MM
    remarks = db.Column(db.Text, nullable=True)  # Optional
    questions = db.relationship('Question', backref='quiz', cascade="all, delete", passive_deletes=True)
    results = db.relationship('QuizResult', backref='quiz', lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=True)
    option4 = db.Column(db.String(200), nullable=True)
    correct_option = db.Column(db.String(10), nullable=False)  # e.g., 'option1', 'option2'
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)  # Email
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    quizzes_taken = db.relationship('QuizResult', backref='student', lazy=True)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False)
    feedback = db.Column(db.Text, nullable=True)  # Optional feedback or remarks
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

# Function to create admin user
def create_admin():
    with app.app_context():
        admin_user = Admin.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = Admin(
                username="admin",
                password=generate_password_hash("87654321"),
                is_admin=True,
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")

# Initialize the database and create admin user
with app.app_context():
    db.create_all()
    create_admin()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")



@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "87654321":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    # Clear the session or any user-specific data
    session.pop('user_id', None) 
    # Redirect to the home page (index.html)
    return redirect(url_for('home'))


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # Fetching data for the dashboard
    students = Student.query.all()  
    subjects = Subject.query.all()  
    quizzes = Quiz.query.all()  
    results = QuizResult.query.all() 
    Chapters = Chapter.query.all()
    return render_template('admin_dashboard.html', students=students, subjects=subjects, quizzes=quizzes, results=results,  Chapters=Chapters)


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']  # This is the email
        password = request.form['password']

        # Check if the student exists
        student = Student.query.filter_by(username=username).first()  # Use email as username in the query
        
        if student and check_password_hash(student.password, password):  # Validate password
            session['student_logged_in'] = True
            session['student_id'] = student.id  # Store the student ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard', student_id=student.id))  # Pass the student ID
            
        flash('Invalid email or password. Please try again.', 'danger')
        
    return render_template('student_login.html')


# Route for student registration
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification')
        dob_str = request.form.get('dob')  # Getting dob as a string (e.g., '2024-12-30')

        # Check if the username is already taken
        existing_student = Student.query.filter_by(username=username).first()
        if existing_student:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('student_register'))

        # Convert the dob string to a Python date object
        if dob_str:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()  # Convert to date object

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new student record
        new_student = Student(
            username=username,
            password=hashed_password,
            full_name=full_name,
            qualification=qualification,
            dob=dob  # Passing the date object here
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_register.html')


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        subject_name = request.form['subject_name']
        subject_description = request.form['subject_description']

        new_subject = Subject(name=subject_name, description=subject_description)
        db.session.add(new_subject)
        db.session.commit()
        
        flash('New subject added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_subject.html')  # Ensure this file exists for GET request



@app.route('/create_chapter/<int:subject_id>', methods=['GET', 'POST'])
def create_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Get the subject by ID
    if request.method == 'POST':
        chapter_name = request.form['chapter_name']
        chapter_description = request.form['chapter_description']

        # Create a new chapter and add to the database
        new_chapter = Chapter(
            name=chapter_name,
            description=chapter_description,
            subject_id=subject_id
        )
        db.session.add(new_chapter)
        db.session.commit()

        flash('Chapter created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_chapter.html', subject_id=subject_id)

@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Get the subject by ID

    if request.method == 'POST':
        subject.name = request.form['subject_name']
        subject.description = request.form['subject_description']

        db.session.commit()  # Save changes to the database
        flash('Subject details updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard

    return render_template('edit_subject.html', subject=subject)


@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    # Delete all chapters associated with this subject
    for chapter in subject.chapters:
        db.session.delete(chapter)
    # Now delete the subject itself
    db.session.delete(subject)
    db.session.commit()
    flash('Subject and its chapters deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        chapter.name = request.form['chapter_name']
        chapter.description = request.form['chapter_description']
        db.session.commit()  # Save the updated chapter in the database
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard

    return render_template('edit_chapter.html', chapter=chapter)  # Render the edit form with current chapter details



# Route to delete a chapter
@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    # Deleting all related quizzes first to avoid foreign key constraint issues
    Quiz.query.filter_by(chapter_id=chapter.id).delete()
    # Deleting the chapter
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard


@app.route('/admin/quiz_dashboard', methods=['GET', 'POST'])
def quiz_dashboard():
    if request.method == 'POST':
        # Get form data to create a new quiz
        quiz_name = request.form['quiz_name']
        chapter_id = request.form['chapter_id']
        time_duration = request.form['time_duration']
        date_of_quiz = request.form['date_of_quiz']
        remarks = request.form['remarks']

        # Convert date string to a datetime.date object
        date_of_quiz = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()

        # Create a new quiz and save it to the database
        new_quiz = Quiz(name=quiz_name, chapter_id=chapter_id, time_duration=time_duration, 
                       date_of_quiz=date_of_quiz, remarks=remarks)
        db.session.add(new_quiz)
        db.session.commit()

        flash('New quiz added successfully!', 'success')
        return redirect(url_for('quiz_dashboard'))  

    chapters = Chapter.query.all()  
    quizzes = Quiz.query.all()  
    return render_template('quiz_dashboard.html', chapters=chapters, quizzes=quizzes)



# Route to display form for adding a new quiz
@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        chapter_id = request.form['chapter_id']
        date_of_quiz_str = request.form['date_of_quiz']
        time_duration = request.form['time_duration']
        remarks = request.form.get('remarks', '')

        # Convert the date string to a Python date object
        date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()

        # Create a new quiz object
        new_quiz = Quiz(name=quiz_name, chapter_id=chapter_id, date_of_quiz=date_of_quiz,
                        time_duration=time_duration, remarks=remarks)

        # Add to the database and commit
        db.session.add(new_quiz)
        db.session.commit()

        flash('Quiz added successfully!', 'success')
        return redirect(url_for('quiz_dashboard'))

    # Get all chapters for the select dropdown
    chapters = Chapter.query.all()
    return render_template('add_quiz.html', chapters=chapters)


@app.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        text = request.form['text']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form.get('option3', None)
        option4 = request.form.get('option4', None)
        correct_option = request.form['correct_option']

        new_question = Question(
            text=text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            quiz_id=quiz.id
        )
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('quiz_dashboard'))
    return render_template('add_question.html', quiz=quiz)


@app.route('/view_question/<int:question_id>')
def view_question(question_id):
    # Query the database for the question with the given ID
    question = Question.query.get_or_404(question_id)
    return render_template('view_question.html', question=question)


@app.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapters = Chapter.query.all()  

    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        chapter_id = request.form['chapter_id']
        date_of_quiz_str = request.form['date_of_quiz']
        time_duration = request.form['time_duration']
        remarks = request.form['remarks']

        # Convert date_of_quiz from string to a Python date object
        try:
            date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('edit_quiz', quiz_id=quiz_id))  # Return to edit form

        # Update quiz details
        quiz.name = quiz_name
        quiz.chapter_id = chapter_id
        quiz.date_of_quiz = date_of_quiz
        quiz.time_duration = time_duration
        quiz.remarks = remarks

        # Commit the changes to the database
        db.session.commit()

        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('quiz_dashboard'))  # Redirect to the quiz dashboard after update

    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)


@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    
    if quiz:
        db.session.delete(quiz)  # This will delete the quiz and all related questions due to cascade
        db.session.commit()
        flash("Quiz and its questions have been deleted successfully.", "success")
    else:
        flash("Quiz not found.", "danger")

    return redirect(url_for('quiz_dashboard'))


@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    # Retrieve the question from the database
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        # Update the question's text and options
        question.text = request.form['text']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form.get('option3')  
        question.option4 = request.form.get('option4')  
        question.correct_option = request.form['correct_option']
        
        # Commit the changes to the database
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('quiz_dashboard'))  # Redirect to the quiz dashboard or another page

    return render_template('edit_question.html', question=question)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    # Retrieve the question from the database
    question = Question.query.get_or_404(question_id)
    
    # Delete the question
    db.session.delete(question)
    db.session.commit()

    flash('Question deleted successfully!', 'success')
    return redirect(url_for('quiz_dashboard'))  


@app.route('/student_dashboard/<int:student_id>', methods=['GET'])
def student_dashboard(student_id):
    # Fetch the student by ID
    student = Student.query.get_or_404(student_id)
    # Fetch all quizzes created by the admin
    quizzes_created_by_admin = Quiz.query.all()  
    # Fetch all quiz results for the student
    quizzes_attempted = QuizResult.query.filter_by(student_id=student_id).all()
    return render_template('student_dashboard.html', student=student, quizzes_created_by_admin=quizzes_created_by_admin, quizzes_attempted=quizzes_attempted)


@app.route('/quiz_details/<int:quiz_id>', methods=['GET'])
def quiz_details(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    student_id = session.get('student_id')  
    student = Student.query.get_or_404(student_id)
    return render_template('quiz_details.html', quiz=quiz, student=student)


@app.route('/start_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def start_quiz(quiz_id):
    # Fetch the quiz and its questions
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for('student_dashboard', student_id=session.get('student_id')))

    # Parse the time_duration (in HH:MM format) to seconds
    time_duration_in_seconds = 0
    if quiz.time_duration:
        try:
            hours, minutes = map(int, quiz.time_duration.split(':'))
            time_duration_in_seconds = (hours * 3600) + (minutes * 60)
        except ValueError:
            flash("Invalid time duration format!", "danger")
            return redirect(url_for('student_dashboard', student_id=session.get('student_id')))

    if request.method == 'POST':
        # Process student's answers
        total_score = 0
        for question in quiz.questions:
            # Retrieve the submitted answer for each question
            student_answer = request.form.get(f"question_{question.id}")
            # Compare with the correct answer
            if student_answer == question.correct_option:
                total_score += 1

        # Record the result
        new_result = QuizResult(
            score=total_score,
            time_stamp=datetime.now(),
            feedback=None,  # Add feedback if needed
            student_id=session.get('student_id'),  
            quiz_id=quiz_id
        )
        db.session.add(new_result)
        db.session.commit()

        flash(f"You scored {total_score}/{len(quiz.questions)}", "success")
        return redirect(url_for('student_dashboard', student_id=session.get('student_id')))

    return render_template('start_quiz.html', quiz=quiz, time_duration=time_duration_in_seconds)


@app.route('/student_scores/<int:student_id>', methods=['GET'])
def student_scores(student_id):
    # Fetch student details (if necessary)
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for('student_dashboard', student_id=session.get('student_id')))
    
    # Fetch the quiz results for the student
    quiz_results = QuizResult.query.filter_by(student_id=student_id).all()

    # If no results found
    if not quiz_results:
        flash("You have not attempted any quizzes yet.", "warning")
    
    return render_template('student_scores.html', student=student, quiz_results=quiz_results)


@app.route('/student_summary/<int:student_id>')
def student_summary(student_id):
    student = Student.query.get_or_404(student_id)

    # Fetch quiz attempts by this student
    attempts = QuizResult.query.filter_by(student_id=student_id).all()
    
    # Count the number of attempts per quiz
    quiz_attempts = {}
    for attempt in attempts:
        quiz_name = attempt.quiz.name
        quiz_attempts[quiz_name] = quiz_attempts.get(quiz_name, 0) + 1

    # Prepare data for the pie chart
    quiz_names = list(quiz_attempts.keys())
    attempt_counts = list(quiz_attempts.values())

    # Generate random colors for the pie chart
    pie_colors = np.random.rand(len(quiz_names), 3)

    # Create the Pie Chart
    plt.figure(figsize=(8, 8))
    plt.pie(attempt_counts, labels=quiz_names, autopct=lambda p: '{:.0f}'.format(p * sum(attempt_counts) / 100),
            colors=pie_colors, startangle=140)
    plt.title(f'Quiz Attempt Summary')
    plt.tight_layout()  # Ensure everything fits without clipping
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    quiz_graph = base64.b64encode(img.getvalue()).decode('utf8')

    # Generate Bar Graph for number of quizzes per subject
    subject_quiz_count = {}
    quizzes = Quiz.query.all()
    for quiz in quizzes:
        subject_name = quiz.chapter.subject.name
        subject_quiz_count[subject_name] = subject_quiz_count.get(subject_name, 0) + 1
    
    subjects = list(subject_quiz_count.keys())
    quiz_counts = list(subject_quiz_count.values())

    # Generate random colors for each bar in the bar chart
    bar_colors = np.random.rand(len(subjects), 3)  # Random colors for each bar
    
    plt.figure(figsize=(10, 6))
    plt.bar(subjects, quiz_counts, color=bar_colors)  # Set the color argument here
    plt.xlabel('Subject')
    plt.ylabel('Number of Quizzes')
    plt.title('Number of Quizzes per Subject')
    plt.xticks(rotation=45, ha='right')  # Rotate subject names for better readability
    plt.tight_layout()  # Ensure everything fits without clipping
    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    subject_graph = base64.b64encode(img2.getvalue()).decode('utf8')

    return render_template('student_summary.html', student=student, quiz_graph=quiz_graph, subject_graph=subject_graph)



@app.route('/admin_summary')
def admin_summary():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    # Fetching data for the dashboard
    students = Student.query.all()
    subjects = Subject.query.all()
    quizzes = Quiz.query.all()
    results = QuizResult.query.all()
    chapters = Chapter.query.all()

    # Calculate the number of quiz attempts for each subject
    subject_attempts = {}
    for quiz in quizzes:
        subject_name = quiz.chapter.subject.name
        subject_attempts[subject_name] = subject_attempts.get(subject_name, 0) + len(QuizResult.query.filter_by(quiz_id=quiz.id).all())

    # Plotting the pie chart with actual numbers (attempts)
    labels = list(subject_attempts.keys())
    sizes = list(subject_attempts.values())

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))  # Creating a subplot for both pie and bar charts
    
    # Pie chart function (same as before)
    def func(pct, allvals):
        absolute = int(pct / 100. * sum(allvals))  # Calculate the number of attempts
        return f"{absolute}"

    ax[0].pie(sizes, labels=labels, autopct=lambda pct: func(pct, sizes), startangle=90)
    ax[0].axis('equal')  # Equal aspect ratio ensures the pie is drawn as a circle.
    ax[0].set_title('Subject-wise Quiz Attempts')

    # Calculate top scores for each subject and convert them to percentage
    subject_top_scores = {}
    for quiz in quizzes:
        subject_name = quiz.chapter.subject.name
        
        # Calculate the total number of questions for the quiz by querying the related Question model
        total_questions = len(Question.query.filter_by(quiz_id=quiz.id).all())  # Assuming Question is related to Quiz
        
        # Get the maximum score for this quiz
        top_score = max([result.score for result in QuizResult.query.filter_by(quiz_id=quiz.id).all()], default=0)
        
        # Calculate percentage score assuming max possible score is equal to the number of questions
        percentage = (top_score / total_questions) * 100 if total_questions > 0 else 0
        subject_top_scores[subject_name] = max(subject_top_scores.get(subject_name, 0), percentage)

    # Bar chart for top scores in percentage
    subject_names = list(subject_top_scores.keys())
    top_scores_percentage = list(subject_top_scores.values())

    ax[1].bar(subject_names, top_scores_percentage, color='skyblue')
    ax[1].set_xlabel('Subjects')
    ax[1].set_ylabel('Top Score (%)')
    ax[1].set_title('Subject-wise Top Scores (Percentage)')

    # Adjust y-axis to display percentage scale
    ax[1].set_ylim(0, 100)  # Ensure the y-axis ranges from 0 to 100 for percentage

    # Save the combined pie and bar chart as a base64-encoded image
    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_image = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('admin_summary.html', students=students, subjects=subjects, quizzes=quizzes, results=results, chapters=chapters, chart_image=chart_image)



@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    query = request.args.get('query', '').strip()  # Get the search query from the form
    search_type = request.args.get('search_type', 'students')  # Get the search type from the dropdown

    # Initialize empty lists for the results
    students = []
    quizzes = []
    subjects = []
    chapters = []
    no_results = False

    # Perform search based on the selected search type
    if query:
        if search_type == 'students':
            students = Student.query.filter(Student.full_name.ilike(f'%{query}%')).all()
        elif search_type == 'quizzes':
            quizzes = Quiz.query.filter(Quiz.name.ilike(f'%{query}%')).all()
        elif search_type == 'subjects':
            subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
        elif search_type == 'chapters':
            chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()

        # If no results are found, set the flag
        if not (students or quizzes or subjects or chapters):
            no_results = True

    return render_template(
        'admin_search.html',
        students=students,
        quizzes=quizzes,
        subjects=subjects,
        chapters=chapters,
        query=query,
        search_type=search_type,
        no_results=no_results  # Pass the flag to the template to display no results message
    )


@app.route('/student_search/<int:student_id>', methods=['GET'])
def student_search(student_id):
    student = Student.query.get_or_404(student_id)

    # Get search parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_marks = request.args.get('min_marks')
    max_marks = request.args.get('max_marks')
    search_term = request.args.get('search_term')  

    # Start building the query for quiz results
    query = QuizResult.query.join(Quiz).join(Chapter).filter(QuizResult.student_id == student_id)

    # Apply date filters if provided
    if start_date:
        query = query.filter(Quiz.date_of_quiz >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Quiz.date_of_quiz <= datetime.strptime(end_date, '%Y-%m-%d'))

    # Apply marks filters if provided
    if min_marks:
        query = query.filter(QuizResult.score >= int(min_marks))
    if max_marks:
        query = query.filter(QuizResult.score <= int(max_marks))

    # Apply quiz name or chapter name filter if provided
    if search_term:
        query = query.filter(
            db.or_(
                Quiz.name.ilike(f'%{search_term}%'),  
                Chapter.name.ilike(f'%{search_term}%')  
            )
        )

    # Execute the query to get results
    search_results = query.all()

    return render_template('student_search.html', student=student, search_results=search_results)



if __name__ == "__main__":
    app.run(debug=True)
