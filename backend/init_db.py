from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User, Role

# Initialize Flask app for database setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Security 
app.config['SECRET_KEY'] = 'super-secret-key-change-later'
app.config['SECURITY_PASSWORD_SALT'] = 'super-secret-salt-change-later'

db.init_app(app)

def setup_database():
    with app.app_context():
        db.create_all()
        
        roles = ['Admin', 'Doctor', 'Patient']
        for role_name in roles:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f'{role_name} privileges')
                db.session.add(role)
        db.session.commit()

        admin_role = Role.query.filter_by(name='Admin').first()
        admin_user = User.query.filter_by(email='admin@hms.com').first()
        
        if not admin_user:
            print("Creating default Admin user...")
            admin_user = User(
                username='superadmin',
                email='admin@hms.com',
                password_hash=generate_password_hash('admin123'), 
                active=True
            )
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print("Success: Admin user 'superadmin' created programmatically!")
        else:
            print("Admin user already exists. Database is ready.")

if __name__ == '__main__':
    setup_database() 