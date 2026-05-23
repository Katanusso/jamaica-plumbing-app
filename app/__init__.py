from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.models import User  # Import User model after initializing db
    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app

app = create_app()
