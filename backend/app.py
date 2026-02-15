from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token
from flask_bcrypt import Bcrypt
from models import db, User, Role
from flask_security import hash_password, verify_password
from flask_security import SQLAlchemyUserDatastore, Security, hash_password
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['JWT_SECRET_KEY'] = 'iitm-hms-secret-key'
app.config['SECURITY_PASSWORD_SALT'] = 'salty-salt'

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and bcrypt.check_password_hash(user.password, data.get('password')):
        # Get the role name for redirection logic
        role = user.roles[0].name
        
        # Create token containing user identity and role info
        access_token = create_access_token(identity={'id': user.id, 'role': role})
        
        return jsonify({
            "access_token": access_token,
            "role": role,
            "message": "Login successful!"
        }), 200

    return jsonify({"message": "Invalid username or password"}), 401
   

# Patient Registration Route
@app.route('/register/patient', methods=['POST'])
def register_patient():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists'}), 400
    
    # Create patient role and user programmatically
    patient_role = Role.query.filter_by(name='patient').first()
    new_user = User(
        username=data['username'],
        password=hash_password(data['password']),
        active=True,
        roles=[patient_role]
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Patient registered successfully'}), 201

# This creates the DB and Admin programmatically
with app.app_context():
    db.create_all()
    # Create Roles if they don't exist
    for r_name in ['admin', 'doctor', 'patient']:
        if not Role.query.filter_by(name=r_name).first():
            db.session.add(Role(name=r_name))
    db.session.commit()
    
    # Create Admin if not exists
    if not User.query.filter_by(username='admin').first():
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_role = Role.query.filter_by(name='admin').first()
        admin_user = User(username='admin', password=hashed_pw, roles=[admin_role])
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)