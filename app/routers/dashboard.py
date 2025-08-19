from flask import Blueprint, request, jsonify, render_template, abort
from ..database import SessionLocal
from .. import crud, schemas
from ..auth import auth_required
from ..whatsapp_client import whatsapp_client
from ..extensions import socketio

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/', methods=['GET'])
@auth_required
def read_dashboard():
    """
    Serves the main dashboard HTML page.
    """
    return render_template("dashboard.html")

@bp.route('/users', methods=['GET'])
@auth_required
def get_all_users():
    """
    Retrieve all users.
    """
    db = SessionLocal()
    try:
        users = crud.get_users(db, skip=0, limit=100)
        # Manually serialize to dicts to avoid circular reference issues with jsonify
        users_data = [{"id": u.id, "whatsapp_id": u.whatsapp_id} for u in users]
        return jsonify(users_data)
    finally:
        db.close()

@bp.route('/users/<int:user_id>/messages', methods=['GET'])
@auth_required
def get_user_messages(user_id: int):
    """
    Retrieve all messages for a specific user.
    """
    db = SessionLocal()
    try:
        messages = crud.get_messages_by_user(db, user_id=user_id)
        # Manually serialize
        messages_data = [
            {"id": m.id, "content": m.content, "direction": m.direction, "timestamp": m.timestamp.isoformat()}
            for m in messages
        ]
        return jsonify(messages_data)
    finally:
        db.close()

@bp.route('/users/<int:user_id>/messages', methods=['POST'])
@auth_required
def send_manual_message(user_id: int):
    """
    Send a manual text message to a user from the dashboard.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        abort(400, description="Missing 'text' in request body")

    text = data['text']
    db = SessionLocal()
    try:
        # This is still inefficient. A get_user_by_id would be better.
        users = crud.get_users(db, limit=1000)
        target_user = next((u for u in users if u.id == user_id), None)

        if not target_user:
            abort(404, description="User not found")

        response = whatsapp_client.send_text_message(to=target_user.whatsapp_id, text=text)
        if not response:
            abort(500, description="Failed to send message via WhatsApp API")

        message_to_save = schemas.MessageCreate(
            content=text,
            direction="outgoing",
            message_type="text",
            whatsapp_message_id=response.get("messages", [{}])[0].get("id")
        )
        created_message = crud.create_message(db, message=message_to_save, user_id=target_user.id)

        # Manually serialize the created message for the response
        message_data = {
            "id": created_message.id,
            "user_id": created_message.user_id,
            "content": created_message.content,
            "direction": created_message.direction,
            "timestamp": created_message.timestamp.isoformat()
        }
        # Emit the new message to all connected dashboard clients
        socketio.emit('new_message', message_data)

        return jsonify(message_data), 201
    finally:
        db.close()
