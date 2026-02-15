from flask import Flask, request , jsonify 
from flask_security import Security, SQLAlchemyUserDatastore, hash_password , verify_password 
from flask_jwt_extended import JWTManager, create_access_token # For token-based auth
from models import db, User, Role
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SECRET_KEY'] = 'iit-madras-super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salty-salt'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key' 

# Flask-Security specific configs
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'

db.init_app(app)
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

with app.app_context():
    db.create_all()
    
    # Create Roles if they don't exist
    if not Role.query.filter_by(name='admin').first():
        user_datastore.create_role(name='admin', description='Hospital Staff')
    if not Role.query.filter_by(name='doctor').first():
        user_datastore.create_role(name='doctor', description='Medical Professional')
    if not Role.query.filter_by(name='patient').first():
        user_datastore.create_role(name='patient', description='User seeking care')
    
    # Create Admin programmatically
    if not User.query.filter_by(username='admin').first():
        user_datastore.create_user(
            username='admin', 
            password=hash_password('admin123'), 
            roles=['admin'],
            fs_uniquifier=str(uuid.uuid4()) # Essential fix
        )
    db.session.commit()


# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    

    if user and verify_password(password, user.password):
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


    

if __name__ == '__main__':
    app.run(debug=True)