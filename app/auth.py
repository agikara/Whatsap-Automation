from functools import wraps
from flask import request, Response
import base64
import secrets
from .config import settings

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return Response(
                'Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})

        # Use secrets.compare_digest for secure string comparison
        user_match = secrets.compare_digest(auth.username, settings.ADMIN_USERNAME)
        pw_match = secrets.compare_digest(auth.password, settings.ADMIN_PASSWORD)

        if not (user_match and pw_match):
            return Response(
                'Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})

        return f(*args, **kwargs)
    return decorated
