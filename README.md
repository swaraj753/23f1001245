# QuizMaster - A Flask-Based Quiz Management System

## 📌 Project Overview
QuizMaster is a web-based application built using Flask that allows students to take quizzes and track their scores. The platform provides an intuitive user interface, secure authentication, and efficient database management.

## 🚀 Features
- **User Authentication**: Secure login/logout for students and administrator.
- **Quiz Management**: Admins can create, edit, and delete quizzes.
- **Attempt Quizzes**: Students can take quizzes and receive instant summary.
- **Score Tracking**: Users can view their quiz scores and performance summaries.
- **Bootstrap UI**: A clean and responsive user interface.

## 🛠️ Technologies Used
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: SQLite

## 📂 Folder Structure
```
mad 1 final project/
├── instance/         # Instance folder for database files
├── templates/        # HTML templates for the application
├── main.py          # Main Flask application file
├── requirements.txt # List of dependencies
```

## 🔧 Installation Guide
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Swaraj753/quizmaster.git
   cd quizmaster
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python app.py
   ```
4. **Access the app:** Open `http://127.0.0.1:5000/` in your browser.

## 📝 Usage Instructions
- **Admin Login:** Create and manage quizzes.
- **Student Login:** Take quizzes and view scores.
- **Logout:** Securely exit the session.

## 🛡️ Security & Best Practices
- Use `Flask-Migrate` for database version control.
- Store sensitive credentials in an `.env` file.
- Ensure user authentication before accessing restricted pages.!

## 📧 Contact
For queries, contact **Swaraj753** on GitHub or via email at `23f1001245@ds.study.iitm.ac.in`. 🚀

