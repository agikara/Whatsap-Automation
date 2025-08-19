from flask import Blueprint, request, Response, abort
from ..config import settings
from ..database import SessionLocal
from .. import crud, schemas
from ..faq_service import faq_service
from ..whatsapp_client import whatsapp_client
from ..extensions import socketio
import logging

bp = Blueprint('webhook', __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bp.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(challenge, status=200)
    else:
        logger.error("Webhook verification failed.")
        abort(403)

@bp.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_json()
    logger.info(f"Received webhook payload: {payload}")
    db = SessionLocal()
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return Response(status=200)

        message_data = messages[0]
        whatsapp_id = message_data.get("from")

        user = crud.get_or_create_user(db, whatsapp_id=whatsapp_id)

        # Onboarding Flow vs. Regular Flow
        if not user.policy_accepted:
            handle_onboarding_flow(db, user, message_data)
        else:
            handle_faq_flow(db, user, message_data)

    except (IndexError, KeyError) as e:
        logger.error(f"Error parsing webhook payload: {e}\nPayload: {payload}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        db.close()

    return Response(status=200)

def handle_onboarding_flow(db: SessionLocal, user: schemas.User, message_data: dict):
    """Handles logic for users who have not accepted the policy."""
    whatsapp_id = user.whatsapp_id
    interaction_type = message_data.get("interactive", {}).get("type")
    selection_id = ""

    if interaction_type == "button_reply":
        selection_id = message_data.get("interactive", {}).get("button_reply", {}).get("id", "")

    if selection_id == "accept_policy":
        crud.update_user_policy_status(db, user_id=user.id, status=True)
        faq_service.get_greeting_message_and_main_menu(to=whatsapp_id)
    else:
        # Send the T&C document and the accept button
        caption = "Welcome! Before we begin, please review our terms and conditions."
        whatsapp_client.send_document(to=whatsapp_id, url=settings.TERMS_AND_CONDITIONS_PDF_URL, caption=caption)

        button = [{"id": "accept_policy", "title": "Accept Policy"}]
        whatsapp_client.send_interactive_reply_buttons(to=whatsapp_id, body_text="Please press accept to continue.", buttons=button)

def handle_faq_flow(db: SessionLocal, user: schemas.User, message_data: dict):
    """Handles the main FAQ logic for users who have accepted the policy."""
    whatsapp_id = user.whatsapp_id
    message_type = message_data.get("type")
    created_message = None

    if message_type == "text":
        content = message_data.get("text", {}).get("body", "")
        created_message = crud.create_message(db, message=schemas.MessageCreate(content=content, direction="incoming"), user_id=user.id)
        if content.lower() in ["hi", "hello", "menu"]:
             faq_service.get_greeting_message_and_main_menu(to=whatsapp_id)
        else:
             faq_service.send_fallback_message(to=whatsapp_id)

    elif message_type == "interactive":
        interactive_data = message_data.get("interactive", {})
        interaction_type = interactive_data.get("type")

        if interaction_type == "button_reply":
            selection_id = interactive_data.get("button_reply", {}).get("id", "")
            content = interactive_data.get("button_reply", {}).get("title", "")
        elif interaction_type == "list_reply":
            selection_id = interactive_data.get("list_reply", {}).get("id", "")
            content = interactive_data.get("list_reply", {}).get("title", "")
        else:
            selection_id = ""
            content = "Unsupported interactive type"

        created_message = crud.create_message(db, message=schemas.MessageCreate(content=content, direction="incoming", message_type="interactive"), user_id=user.id)

        if selection_id:
            faq_service.process_user_selection(to=whatsapp_id, selection_id=selection_id)
        else:
            faq_service.send_fallback_message(to=whatsapp_id)

    elif message_type == "image":
        content = "[User sent an image]"
        created_message = crud.create_message(db, message=schemas.MessageCreate(content=content, direction="incoming", message_type="image"), user_id=user.id)
        whatsapp_client.send_text_message(to=whatsapp_id, text="Thank you, I have received your image.")

    else:
        logger.warning(f"Unsupported message type: {message_type}")

    if created_message:
        message_data = {
            "id": created_message.id,
            "user_id": created_message.user_id,
            "content": created_message.content,
            "direction": created_message.direction,
            "timestamp": created_message.timestamp.isoformat()
        }
        socketio.emit('new_message', message_data)
