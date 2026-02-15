from flask import Flask
from models import db, User, Role
from flask_security import SQLAlchemyUserDatastore, Security, hash_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salty-salt'

db.init_app(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# This creates the DB and Admin programmatically
with app.app_context():
    db.create_all()
    # Create Roles if they don't exist
    if not Role.query.filter_by(name='admin').first():
        user_datastore.create_role(name='admin', description='Hospital Staff')
    if not Role.query.filter_by(name='doctor').first():
        user_datastore.create_role(name='doctor', description='Medical Professional')
    if not Role.query.filter_by(name='patient').first():
        user_datastore.create_role(name='patient', description='User seeking care')
    
    # Create Admin if not exists
    if not User.query.filter_by(username='admin').first():
        user_datastore.create_user(
            username='admin', 
            password=hash_password('admin123'), 
            roles=['admin']
        )
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)