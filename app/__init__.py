from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.database import db

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    
    @app.route('/api/health')
    def health_check():
        return {"status": "ok", "message": "Backend funcionando correctamente"}, 200

    return app