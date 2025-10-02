"""Simple Chat application using Bottle and Beaker sessions.

This module defines the web application routes for authentication, message
posting, and message retrieval. It wires a SessionMiddleware around the
Bottle app to manage user sessions via signed cookies.

Note: Do not use the development debug configuration and the static
session keys in production environments.
"""
import json
import traceback
import bottle as bt
from beaker.middleware import SessionMiddleware
from db_connector import DBConnector
from doughnut_wall import validate_email


session_opts = {
    'session.type': 'cookie',
    'session.cookie_expires': 1200,
    'session.encrypt_key': 'Cisco61!(DieseSpacken516@SollenNichtWissen, das ich no Domain lookup auf allen deren geraten deaktiviert habe um sie bis in den ruin zu treiben, aufgrund dessen das niemand den abbruch shortcut kennt und man sich nun mehr nicht mehr verschreiben das; scheiss Cisco@3411341341341347134!$%&/()=??=)(/&%$"!lgfojidhbsjnkleweguobvhcnkmalodfijvncxmylkcdsfjvn+)',
    'session.validate_key': True,
    'session.auto': True  # wichtig, damit die Session automatisch gespeichert wird
}

db = DBConnector()

# App definieren
bt_app = bt.Bottle()
app = SessionMiddleware(bt_app, session_opts)

# Session-Helferfunktion
def get_session():
    """Return the current Beaker session object associated with the request."""
    return bt.request.environ.get('beaker.session')

def require_authentication(func):
    """Decorator to require authentication for certain routes.

    If the session does not contain a 'email', the user is redirected to
    the login page. Otherwise, the wrapped handler is executed.
    """
    def wrapper(*args, **kwargs):
        session = get_session()
        if 'email' not in session:
            return bt.redirect('/auth')
        return func(*args, **kwargs)
    return wrapper

# Startseite
@bt_app.route('/', method=['GET'])
@require_authentication
def index():
    """Render the chat UI for the currently authenticated user."""
    session = get_session()
    user = session.get('username')
    return bt.template("./tpl/index.html", username=user)

@bt_app.route("/fail", method=['GET'])
def fail():
    """Serve the playful login error page."""
    return bt.static_file("login_error.html", root="./static")

@bt_app.route("/style.css")
def styles():
    """Serve the main stylesheet from the static folder."""
    return bt.static_file("style.css", root="./static")

# Login-Seite
@bt_app.route("/auth", method=['GET', 'POST'])
def auth():
    """Handle login form (GET renders page, POST validates credentials).

    On successful authentication the email is stored in the session and the
    user is redirected to the chat index; otherwise a failure page is shown.
    """
    session = get_session()
    if bt.request.method == 'POST':
        email = bt.request.forms.get('email')
        password = bt.request.forms.get('password')
        valid, username = db.authenticate_user(email, password)
        if valid:
            session['username'] = username
            session["email"] = email
            session.save()  # Speichert die Session!
            return bt.redirect('/')
        else:
            return bt.redirect("/fail")
    return bt.static_file("auth.html", root="./static")

@bt_app.route("/messages", method=["PUT"])
@require_authentication
def add_message():
    """Create a new chat message for the authenticated user.

    Expects a form field named 'msg' in the request body. Returns a simple
    success text response used by the front-end.
    """
    session = get_session()
    email = session.get('email')
    message = bt.request.forms.get('msg')

    if not message:
        return "<p>Message cannot be empty.</p>"

    db.insert_message(email, message)
    return "Message added successfully"

@bt_app.route("/messages", method=["GET"])
@require_authentication
def get_messages():
    """Return messages as JSON, optionally only newer than a given id.

    Query parameter:
      - last_id: if provided, only messages with id greater than this are
        returned; the front-end uses it for incremental updates.
    """
    last_update = bt.request.query.get('last_id', None)
    messages = db.fetch_messages(last_update=last_update)
    bt.response.content_type = 'application/json'
    return json.dumps(messages)

@bt.route("/user/delete", method=['POST'])
@require_authentication
def delete_user():
    """Delete the currently authenticated user and log them out.

    After deletion, the session is cleared and the user is redirected to
    the login page.
    """
    session = get_session()
    email = session.get('email')
    if email:
        try:
            db.delete_user(email)
        except Exception as e:
            traceback.print_exc()
            return bt.abort(text="Error during user deletion.", code=500)
        session.delete()  # Clear session after user deletion
    return bt.redirect('/auth')

@bt.route("/user/change_password", method=['POST'])
@require_authentication
def change_password():
    """Change the password for the currently authenticated user.

    Expects a form field named 'new_password' in the request body.
    After changing the password, the user is redirected to the chat index.
    """
    session = get_session()
    email = session.get('email')
    new_password = bt.request.forms.get('new_password')

    if not new_password:
        return bt.abort(text="New password cannot be empty.", code=400)

    try:
        db.change_user_password(email, new_password)
    except Exception as e:
        traceback.print_exc()
        return bt.abort(text="Error during password change.", code=500)

    return bt.redirect('/')

@bt_app.route("/signup", method=["GET"])
def signup_page():
    """Serve the signup page with client-side confirmation checks."""
    return bt.static_file("signup.html", root="./static")

@bt_app.route("/signup", method=["POST"])
def signup():
    """Register a new user and log them in if successful.

    Validates basic presence of username and password, delegates user
    creation to DBConnector, handles unique constraint errors, and sets
    the session to log in the new user immediately on success.
    """
    username = bt.request.forms.get('username')
    email = bt.request.forms.get('email')
    password = bt.request.forms.get('password')

    if not username or not password or not email or not validate_email(email):
        return bt.redirect("/signup")

    try:
        db.insert_user(email, username, password)
    except Exception as e:
        traceback.print_exc()
        return bt.abort(text="Error during signup - possibly username or email already exists. go back to -> /auth", code=400)
    valid, username = db.authenticate_user(email, password)
    if valid:
        session = get_session()
        session['username'] = username
        session['email'] = email
        session.save()  # Speichert die Session!
        return bt.redirect('/')
    else:
        return bt.redirect("/auth")

# Logout-Route
@bt_app.route("/logout")
def logout():
    """Clear the session and redirect to the login page."""
    session = get_session()
    session.delete()
    return bt.redirect("/auth")
# App starten
if __name__ == '__main__':
    bt.run(app=app, host='localhost', port=8080, debug=True)
