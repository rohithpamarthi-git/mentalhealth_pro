# 🧠 Mental Health Platform

A full-stack web application built with **Python Django** to provide mental health support for students.

## ✨ Features

- 🔐 **Secure User Authentication** — Register, login, and logout
- 🤖 **AI Chatbot** — Generative AI-powered emotional guidance using Google Gemini API
- 📊 **Self-Assessment Module** — Quiz-based mental health scoring and result tracking
- 🩺 **Counselor Request System** — Request sessions with a counselor
- 📚 **Wellness Resources** — Curated mental health articles and tips
- 🎨 **Modern UI** — Premium dark-themed design with smooth animations

## 🛠 Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** SQLite (development)
- **AI Integration:** Google Gemini API

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd mentalhealth_project

# Create a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create a .env file)
# GEMINI_API_KEY=your_api_key_here
# SECRET_KEY=your_django_secret_key

# Apply migrations
python manage.py migrate

# Run the development server
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## 📁 Project Structure

```
mentalhealth_project/
├── mentalhealth_project/   # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── wellness/               # Main app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   └── static/
├── manage.py
├── requirements.txt
└── .gitignore
```

## ⚠️ Environment Variables

Create a `.env` file in the project root (never commit this):
```
SECRET_KEY=your_django_secret_key
GEMINI_API_KEY=your_google_gemini_api_key
DEBUG=True
```

## 📄 License

This project is for educational purposes.
