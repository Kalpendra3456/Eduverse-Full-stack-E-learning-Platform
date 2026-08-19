
import os
import sys

# Add the parent directory to sys.path so we can import 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.extensions import db

def initialize_database():
    print("Initializing database and creating tables...")
    app = create_app()
    with app.app_context():
        db.create_all()
    print("Database initialization complete. All tables created.")

if __name__ == "__main__":
    initialize_database()
