import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuración de lectura de la base de datos PostgreSQL
    db_user = os.getenv('POSTGRES_USER', 'hares_user')
    db_pass = os.getenv('POSTGRES_PASSWORD', 'hares_pass')
    db_host = os.getenv('POSTGRES_HOST', 'db')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'hares_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "ok", 
            "message": "Backend Hares conectado a PostgreSQL correctamente"
        })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)