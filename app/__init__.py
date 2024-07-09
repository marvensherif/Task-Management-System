from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from app.models import init_db
from app.routes import routes
def create_app():
    # creates an instance of the Flask application
    app = Flask(__name__)
    #load config to secure application
    app.config.from_object(Config)
    #pass app instance to handles JWT authentication 
    JWTManager(app)
    #initializes the SQLite database
    init_db()
    routes(app)
    return app