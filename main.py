import json
import traceback
import bottle as bt
from beaker.middleware import SessionMiddleware
from db_connector import DBConnector


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
    return bt.request.environ.get('beaker.session')

def require_authentication(func):
    """Decorator to require authentication for certain routes."""
    def wrapper(*args, **kwargs):
        session = get_session()
        if 'username' not in session:
            return bt.redirect('/auth')
        return func(*args, **kwargs)
    return wrapper

# Startseite
@bt_app.route('/', method=['GET'])
@require_authentication
def index():
    session = get_session()
    user = session.get('username')
    return bt.template("./tpl/index.html", username=user)

@bt_app.route("/fail", method=['GET'])
def fail():
    return bt.static_file("login_error.html", root="./static")

@bt_app.route("/style.css")
def styles():
    return bt.static_file("style.css", root="./static")

# Login-Seite
@bt_app.route("/auth", method=['GET', 'POST'])
def auth():
    session = get_session()
    if bt.request.method == 'POST':
        username = bt.request.forms.get('username')
        password = bt.request.forms.get('password')

        if db.authenticate_user(username, password):
            session['username'] = username
            session.save()  # Speichert die Session!
            return bt.redirect('/')
        else:
            return bt.redirect("/fail")
    return bt.static_file("auth.html", root="./static")

@bt_app.route("/messages", method=["PUT"])
@require_authentication
def add_message():
    session = get_session()
    username = session.get('username')
    message = bt.request.forms.get('msg')

    if not message:
        return "<p>Message cannot be empty.</p>"

    db.insert_message(username, message)
    return "Message added successfully"

@bt_app.route("/messages", method=["GET"])
@require_authentication
def get_messages():
    last_update = bt.request.query.get('last_id', None)
    messages = db.fetch_messages(last_update=last_update)
    bt.response.content_type = 'application/json'
    return json.dumps(messages)

@bt_app.route("/signup", method=["GET"])
def signup_page():
    return bt.static_file("signup.html", root="./static")

@bt_app.route("/signup", method=["POST"])
def signup():
    username = bt.request.forms.get('username')
    password = bt.request.forms.get('password')

    if not username or not password:
        return bt.redirect("/signup")

    try:
        db.insert_user(username, password)
    except Exception as e:
        traceback.print_exc()
        return bt.abort(text="Error during signup - possibly username already exists. go back to -> /auth", code=400)

    if db.authenticate_user(username, password):
        session = get_session()
        session['username'] = username
        session.save()  # Speichert die Session!
        return bt.redirect('/')
    else:
        return bt.redirect("/auth")

# Logout-Route
@bt_app.route("/logout")
def logout():
    session = get_session()
    session.delete()
    return bt.redirect("/auth")
# App starten
if __name__ == '__main__':
    bt.run(app=app, host='localhost', port=8080, debug=True)
