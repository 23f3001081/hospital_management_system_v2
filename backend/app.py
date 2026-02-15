from flask import Flask, request, jsonify 
from flask_security import Security, SQLAlchemyUserDatastore, hash_password, verify_password, auth_required, roles_accepted
from flask_jwt_extended import JWTManager, create_access_token 
from flask_cors import CORS 
from models import db, User, Role, Department # Added Department to imports
import uuid

app = Flask(__name__)

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SECRET_KEY'] = 'iit-madras-super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salty-salt'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key' 

# Flask-Security specific configs
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

# --- Initialize Extensions ---
db.init_app(app)
CORS(app) # Allows your VueJS frontend to talk to this API
jwt = JWTManager(app)

# Setup Flask-Security datastore
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# --- Database & Pre-seeding Logic ---
with app.app_context():
    db.create_all()
    
    # 1. Create Roles if they don't exist
    for r_name in ['admin', 'doctor', 'patient']:
        if not Role.query.filter_by(name=r_name).first():
            user_datastore.create_role(name=r_name)
    
    # 2. Create Admin programmatically
    if not User.query.filter_by(username='admin').first():
        user_datastore.create_user(
            username='admin', 
            password=hash_password('admin123'), 
            roles=['admin'],
            fs_uniquifier=str(uuid.uuid4()) # Required for Flask-Security 4.0+
        )

    # 3. Create Default Departments
    depts = ['Cardiology', 'General Medicine', 'Orthopedics', 'Pediatrics', 'Neurology', 'Dermatology', 'Gynecology']
    for dept_name in depts: 
        if not Department.query.filter_by(name=dept_name).first():
            db.session.add(Department(name=dept_name, description=f"{dept_name} Department")) 
    
    db.session.commit()

# --- Authentication Routes ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if user and verify_password(password, user.password):
        role = user.roles[0].name
        # Token includes the user's role for frontend redirection logic
        access_token = create_access_token(identity={'id': user.id, 'role': role})
        
        return jsonify({
            "access_token": access_token,
            "role": role,
            "message": "Login successful!"
        }), 200

    return jsonify({"message": "Invalid username or password"}), 401

@app.route('/register/patient', methods=['POST'])
def register_patient():
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'User already exists'}), 400
    
    # Use user_datastore to ensure fs_uniquifier is handled correctly
    user_datastore.create_user(
        username=data.get('username'),
        password=hash_password(data.get('password')),
        roles=['patient'],
        fs_uniquifier=str(uuid.uuid4()), # Essential fix for register route
        active=True
    )
    db.session.commit()
    return jsonify({'message': 'Patient registered successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)