from flask import Flask, request, jsonify
from flask_security import Security, SQLAlchemyUserDatastore, hash_password, verify_password, auth_required, roles_accepted
from flask_security.utils import login_user
from flask_cors import CORS
from models import db, User, Role, Department, Doctor, Patient, Appointment
import uuid

app = Flask(__name__)

# --- Configuration (Must be before Security init) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SECRET_KEY'] = 'iit-madras-super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salty-salt'

# ✅ Flask-Security 4.x identity config
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = [
    {"username": {"mapper": lambda x: x}}
]

app.config['SECURITY_USERNAME_ENABLE'] = True
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_TOKEN_MAX_AGE'] = 3600  # 1 hour
app.config['SECURITY_TOKEN_AUTHENTICATION_KEY'] = 'auth_token'  # ensures token support

# --- Initialize Extensions ---
db.init_app(app)
CORS(app)

# Setup Flask-Security datastore and extension
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_blueprint=False)

# --- Database & Pre-seeding Logic ---
with app.app_context():
    db.create_all()

    # Create Roles if they don't exist
    for r_name in ['admin', 'doctor', 'patient']:
        if not Role.query.filter_by(name=r_name).first():
            user_datastore.create_role(name=r_name)

    # Admin Creation Block
    if not User.query.filter_by(username='admin').first():
        admin_role = user_datastore.find_role('admin')
        user_datastore.create_user(
            username='admin',
            email='admin@hms.com',
            password=hash_password('admin123'),
            roles=[admin_role],
            fs_uniquifier=str(uuid.uuid4()),
            active=True
        )

    # Create default departments
    depts = ['Cardiology', 'General Medicine', 'Orthopedics', 'Pediatrics', 'Neurology', 'Dermatology', 'Gynecology']
    for dept_name in depts:
        if not Department.query.filter_by(name=dept_name).first():
            db.session.add(Department(name=dept_name, description=f"{dept_name} Department"))

    db.session.commit()

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    return "HMS Backend Running"

# ✅ Safe login route (handles GET & missing JSON)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return jsonify({"message": "Send POST request with JSON to login"}), 200

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400

    user = User.query.filter_by(username=data.get('username')).first()

    if user and verify_password(data.get('password'), user.password):
        login_user(user)
        token = user.get_auth_token()

        role = user.roles[0].name if user.roles else None

        return jsonify({
            "token": token,
            "role": role,
            "message": "Login successful!"
        }), 200

    return jsonify({"message": "Invalid username or password"}), 401


@app.route('/register/patient', methods=['POST'])
def register_patient():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400

    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'User already exists'}), 400

    patient_role = user_datastore.find_role('patient')

    new_user = user_datastore.create_user(
        username=data.get('username'),
        email=data.get('email', f"{data.get('username')}@hms.com"),
        password=hash_password(data.get('password')),
        roles=[patient_role],
        fs_uniquifier=str(uuid.uuid4()),
        active=True
    )

    new_patient = Patient(
        user=new_user,
        contact=data.get('contact'),
        address=data.get('address')
    )
    db.session.add(new_patient)
    db.session.commit()

    return jsonify({'message': 'Patient registered successfully'}), 201


@app.route('/admin/stats', methods=['GET'])
@auth_required('token')
@roles_accepted('admin')
def get_admin_stats():
    stats = {
        "total_doctors": Doctor.query.count(),
        "total_patients": Patient.query.count(),
        "total_appointments": Appointment.query.count()
    }
    return jsonify(stats), 200


@app.route('/admin/add-doctor', methods=['POST'])
@auth_required('token')
@roles_accepted('admin')
def add_doctor():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username already exists"}), 400

    doctor_role = user_datastore.find_role('doctor')

    new_user = user_datastore.create_user(
        username=data['username'],
        email=data.get('email', f"{data['username']}@hms.com"),
        password=hash_password(data['password']),
        roles=[doctor_role],
        fs_uniquifier=str(uuid.uuid4()),
        active=True
    )

    new_doctor = Doctor(
        user=new_user,
        department_id=data['department_id'],
        specialization=data['specialization'],
        availability=data['availability']
    )
    db.session.add(new_doctor)
    db.session.commit()

    return jsonify({"message": "Doctor added successfully"}), 201


# ... Keep other admin routes (appointments, toggle-user) as they were

if __name__ == '__main__':
    app.run(debug=True)
