
import sys, os
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from backend.extensions import db
from backend.app import create_app

app = create_app()
with app.app_context():
    # Check if record exists
    sql_check = text("SELECT * FROM users WHERE id = 6 AND name = 'test'")
    result = db.session.execute(sql_check).fetchone()
    
    if result:
        print(f"Found record: {result}")
        # Delete record
        sql_delete = text("DELETE FROM users WHERE id = 6 AND name = 'test'")
        db.session.execute(sql_delete)
        db.session.commit()
        print("Record deleted successfully.")
    else:
        # Check if table is 'teachers' or 'users' (User model with role teacher)
        # Based on models.py, it's likely 'users' table
        print("Record not found in 'users' table.")
        
        # Double check 'teachers' table just in case
        try:
            sql_check_t = text("SELECT * FROM teachers WHERE id = 6 AND name = 'test'")
            result_t = db.session.execute(sql_check_t).fetchone()
            if result_t:
                print(f"Found record in 'teachers': {result_t}")
                sql_delete_t = text("DELETE FROM teachers WHERE id = 6 AND name = 'test'")
                db.session.execute(sql_delete_t)
                db.session.commit()
                print("Record deleted successfully from 'teachers' table.")
            else:
                print("Record not found in 'teachers' table either.")
        except Exception as e:
            print(f"Could not check 'teachers' table: {e}")
