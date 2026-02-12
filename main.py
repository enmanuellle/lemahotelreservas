from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config   # ← importa la clase Config
from models import db, Usuario

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)   # ← carga toda la configuración

    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    from routes import auth, main as main_blueprint, api
    app.register_blueprint(auth)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)