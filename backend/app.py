# backend/app.py

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

from extensions import db, migrate, jwt, scheduler
from routes.chatbot import chatbot_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.agent import agent_bp

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG for detailed logs
        format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    scheduler.start()  # Start the APScheduler

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agent_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
