from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from backend.config import Config
from backend.database import db
from backend.database import User

# Inicializar Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar base de datos
db.init_app(app)

# Login
login_manager = LoginManager()
login_manager.login_view = 'web_routes.login'
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
from backend.routes.web import web_routes
app.register_blueprint(web_routes)

with app.app_context():
    db.create_all()

