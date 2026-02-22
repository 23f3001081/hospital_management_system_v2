from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from functools import wraps
from models import db, User, Role, Patient, Doctor, Department, Appointment 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-super-secret-jwt-key' # Used to encrypt tokens

db.init_app(app)
CORS(app) 
jwt = JWTManager(app)

# ==========================================
# 2. ROLE-BASED ACCESS CONTROL (RBAC) DECORATORS
# ==========================================
# This section creates "locks" for our doors. We will put these locks on 
# specific routes later so only the right people can get in.

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if current_user.get('role') == required_role:
                return fn(*args, **kwargs)
            else:
                return jsonify({'message': f'Access forbidden: {required_role}s only'}), 403
        return decorator
    return wrapper

# These are the actual locks we will use later
admin_required = role_required('Admin')
doctor_required = role_required('Doctor')
patient_required = role_required('Patient')


# ==========================================
# 3. AUTHENTICATION ROUTES (Login & Register)
# ==========================================

@app.route('/api/login', methods=['POST'])
def login():
    """Universal login for Admins, Doctors, and Patients."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        user_role = user.roles[0].name if user.roles else 'Unknown'
        
        # Give the user a digital keycard (token)
        access_token = create_access_token(identity={'id': user.id, 'role': user_role})
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'role': user_role,
            'username': user.username
        }), 200

    return jsonify({'message': 'Invalid email or password'}), 401


@app.route('/api/register/patient', methods=['POST'])
def register_patient():
    """Only patients can register themselves."""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'email', 'password', 'contact')):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already taken'}), 409

    patient_role = Role.query.filter_by(name='Patient').first()
    
    # Save the basic user info
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        active=True
    )
    new_user.roles.append(patient_role)
    db.session.add(new_user)
    db.session.flush() 

    # Save the specific patient info
    new_patient = Patient(
        user_id=new_user.id,
        contact=data['contact'],
        address=data.get('address', '')
    )
    db.session.add(new_patient)
    db.session.commit()

    return jsonify({'message': 'Patient registered successfully'}), 201

# Admin Dashboard 

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard_stats():
    """Dashboard: show total patients, doctors, appointments."""
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    
    return jsonify({
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments
    }), 200

@app.route('/api/admin/doctor/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor(doctor_id):
    """Add and update doctor profiles (Update portion)."""
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    data = request.get_json()
    
    if 'specialization' in data:
        doctor.specialization = data['specialization']
    if 'availability' in data:
        doctor.availability = data['availability']
    
    db.session.commit()
    return jsonify({'message': 'Doctor updated successfully'}), 200

@app.route('/api/admin/doctors/search', methods=['GET'])
@admin_required
def search_doctors():
    """Search doctors (by name/specialization)."""
    query = request.args.get('q', '')
    
    # Search by specialization or the linked User's username
    doctors = Doctor.query.join(User).filter(
        (Doctor.specialization.ilike(f'%{query}%')) | 
        (User.username.ilike(f'%{query}%'))
    ).all()
    
    results = [{'id': doc.id, 'name': doc.user.username, 'specialization': doc.specialization} for doc in doctors]
    return jsonify(results), 200

@app.route('/api/admin/patients/search', methods=['GET'])
@admin_required
def search_patients():
    """Search patients (by name/ID/contact)."""
    query = request.args.get('q', '')
    
    patients = Patient.query.join(User).filter(
        (Patient.contact.ilike(f'%{query}%')) | 
        (User.username.ilike(f'%{query}%')) |
        (User.id == int(query) if query.isdigit() else False)
    ).all()
    
    results = [{'id': p.id, 'name': p.user.username, 'contact': p.contact} for p in patients]
    return jsonify(results), 200

@app.route('/api/admin/appointments', methods=['GET'])
@admin_required
def view_all_appointments():
    """View/manage all appointments (upcoming & past)."""
    appointments = Appointment.query.all()
    results = [{
        'id': appt.id,
        'doctor': appt.doctor.user.username,
        'patient': appt.patient.user.username,
        'date': str(appt.date),
        'time': str(appt.time),
        'status': appt.status
    } for appt in appointments]
    
    return jsonify(results), 200

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    """Blacklist/remove doctors & patients from the system."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    if 'Admin' in [role.name for role in user.roles]:
        return jsonify({'message': 'Cannot delete an Admin'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'User {user.username} has been removed from the system'}), 200

# ==========================================
# 4. START THE SERVER
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)