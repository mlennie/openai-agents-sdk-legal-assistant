from flask import Flask
from .config import Config
from .api.webhooks import webhook_bp
import logging

def create_app(config_class=Config):
    """Application factory function."""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Set up logging
    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    
    return app 