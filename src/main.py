import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, render_template # Added render_template
from src.models import db # Corrected import for db
from src.models.research_item import ResearchItem # Import the model
from src.routes.main_routes import main_bp # Import main blueprint
from src.routes.admin_routes import admin_bp # Import admin blueprint

app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(__file__), 'static'),
            template_folder=os.path.join(os.path.dirname(__file__), 'templates')) # Define template folder

# --- Configurations ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key_for_dev_!@#$') # Use env var or fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"postgresql://{os.getenv('DB_USERNAME', 'user')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'mydb')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "static", "uploads")

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- Initialize DB ---
db.init_app(app)
with app.app_context():
    # Import models here if they are defined elsewhere and needed for create_all
    # from src.models.research_item import ResearchItem 
    db.create_all() # Create tables based on models

# --- Register Blueprints ---
app.register_blueprint(main_bp) 
app.register_blueprint(admin_bp)

# --- Error Handling (Optional but recommended) ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 # Assuming you create a 404.html template

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500 # Assuming you create a 500.html template

# --- Run Application ---
if __name__ == '__main__':
    # Make sure to set debug=False for production
    app.run(host=\'0.0.0.0\', port=5000, debug=False)


# --- S3/Cloudflare R2 Configuration ---
app.config["S3_ENDPOINT_URL"] = os.environ.get("S3_ENDPOINT_URL")
app.config["S3_ACCESS_KEY_ID"] = os.environ.get("S3_ACCESS_KEY_ID")
app.config["S3_SECRET_ACCESS_KEY"] = os.environ.get("S3_SECRET_ACCESS_KEY")
app.config["S3_BUCKET_NAME"] = os.environ.get("S3_BUCKET_NAME")

