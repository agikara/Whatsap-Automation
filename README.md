# Advanced WhatsApp FAQ Bot with Real-Time Dashboard

This project is a complete, full-stack WhatsApp FAQ and support automation system built with Python and Flask. It integrates with the official Meta WhatsApp Business Cloud API to provide an advanced, interactive experience for users, including a new-user onboarding flow.

This V2 of the project includes a real-time admin dashboard for seamless chat management, and support for multimedia messages.

## V2 Advanced Features

- **New User Onboarding:**
  - First-time users are greeted with a welcome message and a PDF of the terms and conditions.
  - The conversation only proceeds after the user accepts the policy via an interactive button.
- **Image Messaging Support:**
  - The bot can now send images along with text replies, configured via a URL in the `faq.json` file.
  - The bot acknowledges images sent by the user.
- **Real-Time Admin Dashboard:**
  - The dashboard, now built with **Flask**, features a live-updating chat window.
  - New messages from users or replies sent by the admin appear instantly without needing a page refresh, powered by **WebSockets (Flask-SocketIO)**.

## Core Features

- **Interactive WhatsApp Bot:**
  - Uses interactive List Menus for easy navigation through FAQ categories.
  - Responds with predefined answers from a configurable `faq.json` file.
- **Admin Dashboard:**
  - Securely log in to view a list of all conversations.
  - Select a user to view the full chat history.
  - Send manual text messages to users.
- **Technical:**
  - Built with **Flask**, a lightweight and powerful Python web framework.
  - Uses **SQLAlchemy** for database interactions with a **SQLite** database.
  - All conversations are logged in the database.

## Tech Stack

- **Backend:** Flask, Flask-SocketIO, Gunicorn
- **Database:** SQLite, SQLAlchemy
- **Frontend:** HTML, CSS, Vanilla JavaScript, Socket.IO Client
- **API Integration:** Python `requests` library

## Prerequisites

- Python 3.8+ and Pip
- A Meta for Developers account & a configured WhatsApp Business App

## Setup and Installation

**1. Clone the Repository**
```bash
git clone <repository-url>
cd <repository-name>
```

**2. Create a Virtual Environment**
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**

The application is configured via default values in `app/config.py`. For a real deployment, you should create a `.env` file in the project root to override these defaults.

- You can copy the example file: `cp .env.example .env`
- Open `.env` and fill in the values:
  - `WHATSAPP_TOKEN`: Your access token from the Meta App.
  - `WHATSAPP_PHONE_NUMBER_ID`: The Phone Number ID from the Meta App.
  - `VERIFY_TOKEN`: A secret token you create for webhook verification.
  - `ADMIN_USERNAME` & `ADMIN_PASSWORD`: Credentials for the admin dashboard.
  - `TERMS_AND_CONDITIONS_PDF_URL`: A public URL to your terms and conditions PDF.

## Running the Application

**For Development:**

You can run the application directly using the `run.py` script. This uses the Flask development server with WebSocket support.
```bash
python run.py
```
The server will be running on `http://127.0.0.1:5000`.

**For Production:**

For a production deployment, it is recommended to use a proper WSGI server like Gunicorn.
```bash
gunicorn --worker-class eventlet -w 1 run:app
```

## How to Use

**1. Configure the Webhook**

Your application needs a public URL. For local development, use a tool like **ngrok**.
```bash
ngrok http 5000
```
- In your Meta App Dashboard (WhatsApp > Configuration), set the **Callback URL** to your public URL followed by `/webhook` (e.g., `https://random.ngrok.io/webhook`).
- Set the **Verify token** to the same value as your `VERIFY_TOKEN`.
- Subscribe to the `messages` webhook field.

**2. Access the Admin Dashboard**

- Navigate to `http://127.0.0.1:5000/dashboard` in your browser.
- Log in with the admin credentials.
- You will see conversations appear in the left panel, and new messages will appear in the chat window in real-time.
