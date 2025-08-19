from flask import Flask
from flask_socketio import SocketIO
from .database import create_db_and_tables

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    socketio.init_app(app)

    with app.app_context():
        # Create database tables
        create_db_and_tables()

        # Import and register blueprints
        from .routers import webhook, dashboard
        app.register_blueprint(webhook.bp)
        app.register_blueprint(dashboard.bp)

    return app
