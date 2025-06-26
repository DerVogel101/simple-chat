import bottle as bt
from beaker.middleware import SessionMiddleware
from userbase import authenticate

session_opts = {
    'session.type': 'cookie',
    'session.cookie_expires': 1200,
    'session.encrypt_key': 'Cisco61!(DieseSpacken516@SollenNichtWissen, das ich no Domain lookup auf allen deren geraten deaktiviert habe um sie bis in den ruin zu treiben, aufgrund dessen das niemand den abbruch shortcut kennt und man sich nun mehr nicht mehr verschreiben das; scheiss Cisco@3411341341341347134!$%&/()=??=)(/&%$"!lgfojidhbsjnkleweguobvhcnkmalodfijvncxmylkcdsfjvn+)',
    'session.validate_key': True,
    'session.auto': True  # wichtig, damit die Session automatisch gespeichert wird
}

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
        return f"<h1>Willkommen zurück!</h1><p><a href='/logout'>Logout</a></p>"

@bt_app.route("/fail", method=['GET'])
def fail():
    return bt.static_file("login_error.html", root="./static")
# Login-Seite
@bt_app.route("/auth", method=['GET', 'POST'])
def auth():
    session = get_session()
    if bt.request.method == 'POST':
        username = bt.request.forms.get('username')
        password = bt.request.forms.get('password')
        if authenticate(username, password):
            session['username'] = username
            session.save()  # Speichert die Session!
            return bt.redirect('/')
        else:
            return bt.redirect("/fail")
    return bt.static_file("auth.html", root="./static")

# Logout-Route
@bt_app.route("/logout")
def logout():
    session = get_session()
    session.delete()
    return "<p>Logged out. <a href='/'>Go back</a>.</p>"

# App starten
if __name__ == '__main__':
    bt.run(app=app, host='localhost', port=8080, debug=True)
