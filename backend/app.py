import os
import csv
from datetime import datetime, timedelta
from functools import wraps
import secrets
import string
from celery import Celery
from celery.schedules import crontab

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request,
    jwt_required 
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    Treatment,
    db,
    User,
    Role,
    Patient,
    Doctor,
    Department,
    Appointment
)

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='')

# 1. CONFIGURATION & SETUP
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-super-secret-jwt-key'  
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24) 

# Email configuration 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  
app.config['MAIL_PASSWORD'] = 'your-app-password'  
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

db.init_app(app)
CORS(app)
jwt = JWTManager(app)
from flask_mail import Mail
mail = Mail(app)


from flask_caching import Cache
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/1' 
cache = Cache(app)


def make_celery(app):
    celery = Celery(app.import_name)
    
    celery.conf.update(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        timezone='UTC'
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

celery.conf.beat_schedule = {
    'daily-reminders': {
        'task': 'app.send_daily_reminders',
        'schedule': crontab(hour=8, minute=0), 
    },
    'monthly-reports': {
        'task': 'app.generate_monthly_doctor_report',
        'schedule': crontab(0, 0, day_of_month='1'),
    }
}
 

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('role') == required_role:
                return fn(*args, **kwargs)
            return jsonify({'message': f'Access forbidden: {required_role}s only'}), 403
        return decorator
    return wrapper

admin_required = role_required('Admin')
doctor_required = role_required('Doctor')
patient_required = role_required('Patient')

# Doctor availability 
VALID_AVAILABILITY_OPTIONS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Everyday']

def parse_time_logic(time_str):
    """Helper to parse time strings like '10:00 AM', '1pm', '13:00' into time objects."""
    time_str = time_str.strip().upper()
    formats = ['%I:%M %p', '%I %p', '%I%M %p'] # Strictly AM/PM formats
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    return None

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>.vue', methods=['GET'])
def serve_vue(filename):
    return app.send_static_file(f"{filename}.vue")

@app.route('/<path:filename>.js', methods=['GET'])
def serve_js(filename):
    return app.send_static_file(f"{filename}.js")

@app.route('/<path:filename>.css', methods=['GET'])
def serve_css(filename):
    return app.send_static_file(f"{filename}.css")

#Login & Register

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        user_role = user.roles[0].name if user.roles else 'Unknown'
        access_token = create_access_token(
    identity=str(user.id), 
    additional_claims={'role': user_role}
)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'role': user_role,
            'username': user.username
        }), 200

    return jsonify({'message': 'Invalid email or password'}), 401


@app.route('/api/register', methods=['POST'])
def register_patient():
    """Only patients can register themselves."""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'email', 'password', 'contact')):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already used'}), 409

    patient_role = Role.query.filter_by(name='Patient').first()
    

    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        active=True
    )
    new_user.roles.append(patient_role)
    db.session.add(new_user)
    db.session.flush() 

    
    new_patient = Patient(
        user_id=new_user.id,
        contact=data['contact'],
        address=data.get('address', '')
    )
    db.session.add(new_patient)
    db.session.commit()

    return jsonify({'message': 'Patient registered successfully'}), 201

@app.route('/api/departments', methods=['GET'])
def get_departments():
    departments = Department.query.all()
    results = [{'id': d.id, 'name': d.name, 'description': d.description} for d in departments]
    return jsonify(results), 200


# Admin Dashboard 
@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard_stats():
    cache_key = "admin_dashboard_stats"
    cached = cache.get(cache_key)
    if cached:
        print("\n[CACHE HIT] Admin dashboard loaded\n")
        return jsonify(cached), 200
    
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    
    data = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments
    }
    cache.set(cache_key, data, timeout=300)  
    return jsonify(data), 200

#admin-doctor
@app.route('/api/admin/doctor', methods=['POST'])
@admin_required
def add_doctor():
    data = request.get_json()
    required_fields = ['username', 'email', 'specialization', 'department_name']
    if not all(k in data for k in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already taken'}), 409


    raw_password = data.get('password')
    if not raw_password:
        raw_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))

    
    dept_name = data['department_name']
    department = Department.query.filter_by(name=dept_name).first()
    if not department:
        department = Department(name=dept_name, description="General")
        db.session.add(department)
        db.session.flush() 

    doctor_role = Role.query.filter_by(name='Doctor').first()
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(raw_password),
        active=True
    )
    new_user.roles.append(doctor_role)
    db.session.add(new_user)
    db.session.flush() 


    availability_value = data.get('availability', 'Not specified')
    if availability_value != 'Not specified' and availability_value not in VALID_AVAILABILITY_OPTIONS:
        return jsonify({'message': 'Invalid availability. Must be a day Monday-Saturday.'}), 400

    new_doctor = Doctor(
        user_id=new_user.id,
        department_id=department.id,
        specialization=data['specialization'],
        availability=availability_value,
        time_availability=data.get('time_availability', '10:00 AM - 09:00 PM')
    )
    db.session.add(new_doctor)
    db.session.commit()

    print(f"\n--- DOCTOR CREATED ---")
    print(f"Username: {data['username']}")
    print(f"Generated Password: {raw_password}")
    print(f"----------------------\n")

    return jsonify({
        'message': 'Doctor added successfully!',
        'generated_password': raw_password
    }), 201

@app.route('/api/admin/doctor/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    data = request.get_json()
    
    if 'specialization' in data:
        doctor.specialization = data['specialization']
    if 'availability' in data:
        if data['availability'] not in VALID_AVAILABILITY_OPTIONS:
            return jsonify({'message': 'Invalid availability. Must be a day Monday-Saturday.'}), 400
        doctor.availability = data['availability']
    if 'time_availability' in data:
        doctor.time_availability = data['time_availability']
    if 'name' in data:
        doctor.user.username = data['name']
    
    db.session.commit()
    
    cache.clear() 
    print("[CACHE] Doctor profile updated.")
    
    return jsonify({'message': 'Doctor updated successfully'}), 200

@app.route('/api/admin/doctors', methods=['GET'])
@admin_required
def get_all_doctors():
    doctors = Doctor.query.all()
    results = [{
        'id': doc.id,
        'user_id': doc.user.id,
        'name': doc.user.username,
        'specialization': doc.specialization,
        'department': doc.department.name if doc.department else 'N/A',
        'availability': doc.availability,
        'time_availability': doc.time_availability
    } for doc in doctors]
    return jsonify(results), 200

@app.route('/api/admin/doctor/<int:doctor_id>', methods=['GET'])
@admin_required
def get_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({'message': 'Doctor not found'}), 404
        
    return jsonify({
        'id': doc.id,
        'name': doc.user.username,
        'email': doc.user.email,
        'specialization': doc.specialization,
        'department': doc.department.name if doc.department else 'N/A',
        'availability': doc.availability,
        'time_availability': doc.time_availability
    }), 200

@app.route('/api/admin/doctors/search', methods=['GET'])
@admin_required
def search_doctors():
    query = request.args.get('q', '') 
    doctors = Doctor.query.join(User).filter(
        (Doctor.specialization.ilike(f'%{query}%')) | 
        (User.username.ilike(f'%{query}%'))
    ).all()
    
    results = [{'id': doc.id, 'name': doc.user.username, 'specialization': doc.specialization} for doc in doctors]
    return jsonify(results), 200


#admin-patients
@app.route('/api/admin/patients/search', methods=['GET'])
@admin_required
def search_patients():
    query = request.args.get('q', '')
    
    patients = Patient.query.join(User).filter(
        (Patient.contact.ilike(f'%{query}%')) | 
        (User.username.ilike(f'%{query}%')) |
        (User.id == int(query) if query.isdigit() else False)
    ).all()
    
    results = [{'id': p.id, 'user_id': p.user_id, 'name': p.user.username, 'contact': p.contact, 'address': p.address} for p in patients]
    return jsonify(results), 200

@app.route('/api/admin/patients', methods=['GET'])
@admin_required
def get_all_patients():
    patients = Patient.query.all()
    results = [{
        'id': p.id,
        'user_id': p.user_id,
        'name': p.user.username,
        'email': p.user.email,
        'contact': p.contact,
        'address': p.address
    } for p in patients]
    return jsonify(results), 200

@app.route('/api/admin/patient/<int:patient_id>', methods=['PUT'])
@admin_required
def update_patient_admin(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
         return jsonify({'message': 'Patient not found'}), 404
    data = request.get_json()
    if 'name' in data:
         patient.user.username = data['name']
    if 'contact' in data:
         patient.contact = data['contact']
    if 'address' in data:
         patient.address = data['address']
    db.session.commit()
    return jsonify({'message': 'Patient updated successfully'}), 200

@app.route('/api/admin/appointments', methods=['GET'])
@admin_required
def view_all_appointments():
    appointments = Appointment.query.all()
    results = [{
        'id': appt.id,
        'doctor': appt.doctor.user.username,
        'patient': appt.patient.user.username,
        'date': str(appt.date),
        'time_slot': appt.time_slot,
        'status': appt.status
    } for appt in appointments]
    
    return jsonify(results), 200

@app.route('/api/admin/appointment/<int:appointment_id>', methods=['PUT'])
@admin_required
def update_appointment(appointment_id):
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
        
    data = request.get_json()
    
    if 'status' in data:
        if data['status'] == 'Completed':
            return jsonify({'message': 'Admins cannot mark appointments as Completed. Only doctors can do this through treatment.'}), 400
        appt.status = data['status']
    if 'doctor_id' in data:
        appt.doctor_id = data['doctor_id']
    if 'date' in data:
        appt.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'time_slot' in data:
        appt.time_slot = data['time_slot']
        
    db.session.commit()
    

    cache.delete(f"patient_history_{appt.patient_id}")
    cache.delete(f"doctor_dashboard_{appt.doctor_id}")
    cache.delete("admin_dashboard_stats")
    
    return jsonify({'message': 'Appointment updated successfully'}), 200

@app.route('/api/admin/appointment/<int:appointment_id>', methods=['DELETE'])
@admin_required
def delete_appointment(appointment_id):
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
        
    p_id = appt.patient_id
    d_id = appt.doctor_id
    
    db.session.delete(appt)
    db.session.commit()
    

    cache.delete(f"patient_history_{p_id}")
    cache.delete(f"doctor_dashboard_{d_id}")
    cache.delete("admin_dashboard_stats")
    
    return jsonify({'message': 'Appointment deleted successfully'}), 200

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    if 'Admin' in [role.name for role in user.roles]:
        return jsonify({'message': 'Cannot delete an Admin'}), 403

    db.session.delete(user)
    db.session.commit()
    
    cache.clear()
    print("[CACHE] Admin deleted a user.")
    
    return jsonify({'message': f'User {user.username} is removed.'}), 200

# Doctor Functions
@app.route('/api/doctor/profile', methods=['GET'])
@doctor_required
def get_doctor_profile():
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    return jsonify({
        'name': doctor.user.username,
        'specialization': doctor.specialization,
        'availability': doctor.availability,
        'time_availability': doctor.time_availability
    }), 200

@app.route('/api/doctor/dashboard', methods=['GET'])
@doctor_required
def get_doctor_dashboard():
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    cache_key = f"doctor_dashboard_{doctor.id}"
    cached = cache.get(cache_key)
    if cached:
        print(f"\n[CACHE HIT] Doctor {doctor.id} dashboard loaded.\n")
        return jsonify(cached), 200
    
    today = datetime.now().date()
    end_of_week = today + timedelta(days=7)
    
    upcoming = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= today,
        Appointment.date <= end_of_week,
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.date.asc(), Appointment.time_slot.asc()).all()
    
    data = [{
        'id': a.id,
        'patient_name': a.patient.user.username,
        'date': str(a.date),
        'time_slot': a.time_slot,
        'status': a.status
    } for a in upcoming]
    
    cache.set(cache_key, data, timeout=600) 
    return jsonify(data), 200

@app.route('/api/doctor/patients', methods=['GET'])
@doctor_required
def get_assigned_patients():
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    patients = Patient.query.join(Appointment).filter(Appointment.doctor_id == doctor.id).distinct().all()
    
    return jsonify([{
        'patient_id': p.id,
        'name': p.user.username,
        'contact': p.contact
    } for p in patients]), 200

@app.route('/api/doctor/appointment/<int:appointment_id>', methods=['PATCH'])
@doctor_required
def update_appointment_status(appointment_id):
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    appt = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first()
    if not appt:
        return jsonify({'message': 'Appointment not found '}), 404 
        
    data = request.get_json()
    if 'status' in data:
        if data['status'] not in ['Booked', 'Completed', 'Cancelled']:
            return jsonify({'message': 'Invalid status'}), 400
        appt.status = data['status']
        db.session.commit()
        return jsonify({'message': f'Appointment marked {appt.status}'}), 200
        
    return jsonify({'message': 'No status provided'}), 400

@app.route('/api/doctor/treatment', methods=['POST']) 
@doctor_required
def add_treatment():
    
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    data = request.get_json()
    appt_id = data.get('appointment_id')
    
    appt = Appointment.query.filter_by(id=appt_id, doctor_id=doctor.id).first()
    if not appt:
        return jsonify({'message': 'Appointment not found.'}), 404
        
    if appt.treatment:
         appt.treatment.diagnosis = data.get('diagnosis', appt.treatment.diagnosis)
         appt.treatment.prescription = data.get('prescription', appt.treatment.prescription)
         appt.treatment.notes = data.get('notes', appt.treatment.notes)
    else:
        new_treatment = Treatment(
            appointment_id=appt.id,
            diagnosis=data.get('diagnosis'),
            prescription=data.get('prescription'),
            notes=data.get('notes')
        )
        db.session.add(new_treatment)
        
    appt.status = 'Completed' 
    db.session.commit()
    
    cache.delete(f"patient_history_{appt.patient_id}")
    cache.delete(f"doctor_dashboard_{appt.doctor_id}")
    cache.delete("admin_dashboard_stats")
    print("[CACHE] Patient history, doctor dashboard, and admin stats caches cleared.")
    
    return jsonify({'message': 'Treatment saved!'}), 201

@app.route('/api/doctor/availability', methods=['PUT'])
@doctor_required
def update_doctor_availability():
    user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    data = request.get_json()
    
    if 'availability' in data:
        if data['availability'] not in VALID_AVAILABILITY_OPTIONS:
            return jsonify({'message': 'Invalid availability. Must be a day Monday-Saturday.'}), 400

        doctor.availability = data['availability']
        
    if 'time_availability' in data:
        doctor.time_availability = data['time_availability']
        
    db.session.commit()
        
    cache.delete(f"doctor_{doctor.id}_availability")
    cache.clear() 
    print(f"\n[CACHE] Doctor {doctor.id} updated their availability.\n")
        
    return jsonify({'message': 'Availability updated.'}), 200
        
    return jsonify({'message': 'No availability provided.'}), 400

    
# patient functions
@app.route('/api/patient/profile', methods=['PUT'])
@patient_required
def update_patient_profile():
    user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=user_id).first()
    data = request.get_json()
    
    updated = False
    if 'contact' in data:
        patient.contact = data['contact']
        updated = True
    if 'address' in data:
        patient.address = data['address']
        updated = True
        
    if updated:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200
        
    return jsonify({'message': 'No fields provided to update.'}), 400

@app.route('/api/patient/doctors/search', methods=['GET'])
@patient_required
def patient_search_doctors():
    query = request.args.get('q', '')
    
    cache_key = f"patient_search_docs_{query}"
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        print(f"\n[CACHE HIT] Loaded Patient Search '{query}'\n")
        return jsonify(cached_results), 200
        
    print(f"\n[CACHE MISS] '{query}'...\n")
    
    doctors = Doctor.query.join(User).filter(
        (Doctor.specialization.ilike(f'%{query}%')) | 
        (User.username.ilike(f'%{query}%')) |
        (Doctor.availability.ilike(f'%{query}%'))
    ).all()
    
    results = [{
        'id': doc.id, 
        'name': doc.user.username, 
        'specialization': doc.specialization,
        'department': doc.department.name if doc.department else 'N/A',
        'availability': doc.availability,
        'time_availability': doc.time_availability
    } for doc in doctors]
    
    cache.set(cache_key, results, timeout=3600) 
    return jsonify(results), 200

@app.route('/api/doctor/<int:doctor_id>/availability', methods=['GET'])
@patient_required
def get_doctor_availability(doctor_id):
    cache_key = f"doctor_{doctor_id}_availability"
    cached = cache.get(cache_key)
    if cached is not None:
        print(f"\n[CACHE HIT] Delivering Doctor {doctor_id} availability perfectly from Redis!\n")
        return jsonify(cached), 200
        
    print(f"\n[CACHE MISS] Querying database for Doctor {doctor_id} availability...\n")
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({'message': 'Doctor not found'}), 404
        
    results = {
        'id': doc.id,
        'name': doc.user.username,
        'specialization': doc.specialization,
        'availability': doc.availability
    }
    cache.set(cache_key, results, timeout=600)
    return jsonify(results), 200

@app.route('/api/patient/appointments/book', methods=['POST'])
@patient_required
def book_appointment():
    data = request.get_json()
    user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    appt_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    time_slot = data['time_slot']
    doctor_id = data['doctor_id']

    doctor = Doctor.query.get(doctor_id)
    if doctor:
        if doctor.availability and doctor.availability not in ['Not specified', 'Everyday']:
            if appt_date.strftime('%A') != doctor.availability:
                return jsonify({'message': f'Doctor is only available on {doctor.availability}s'}), 400
        

        if doctor.time_availability and ' - ' in doctor.time_availability:
            start_str, end_str = doctor.time_availability.split(' - ')
            start_time = parse_time_logic(start_str)
            end_time = parse_time_logic(end_str)
            req_time = parse_time_logic(time_slot)
            
            if start_time and end_time and req_time:
                if not (start_time <= req_time <= end_time):
                    return jsonify({'message': f'Doctor is only available between {start_str} and {end_str}'}), 400
            elif not req_time:
                 return jsonify({'message': 'Invalid time format. Please use e.g. 10:00 AM'}), 400


    existing_appt = Appointment.query.filter_by(
        doctor_id=doctor_id, 
        date=appt_date, 
        time_slot=time_slot
    ).filter(Appointment.status != 'Cancelled').first()

    if existing_appt:
        return jsonify({'message': 'Time slot already taken'}), 400

    new_appt = Appointment(
        doctor_id=doctor_id,
        patient_id=patient.id,
        date=appt_date,
        time_slot=time_slot,
        status='Booked'
    )
    db.session.add(new_appt)
    db.session.commit()
    

    cache.delete(f"doctor_{doctor_id}_availability")
    cache.delete(f"patient_history_{patient.id}")
    cache.delete("admin_dashboard_stats")
    print(f"\n[CACHE] Cleared availability and history cache for Patient {patient.id} and Doctor {doctor_id} after new booking.\n")
    
    return jsonify({'message': 'Appointment successfully booked!'}), 201

@app.route('/api/patient/appointment/<int:appointment_id>', methods=['PATCH'])
@patient_required
def manage_patient_appointment(appointment_id):
    user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    appt = Appointment.query.filter_by(id=appointment_id, patient_id=patient.id).first()
    if not appt:
        return jsonify({'message': 'Appointment not found.'}), 404
        
    data = request.get_json()
    
    status = data.get('status')
    if status == 'Cancelled':
        appt.status = 'Cancelled'
        
    new_date = data.get('date')
    new_time_slot = data.get('time_slot')
    

    if new_date and new_time_slot:
        parsed_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        
        if appt.doctor.availability and appt.doctor.availability not in ['Not specified', 'Everyday']:
            if parsed_date.strftime('%A') != appt.doctor.availability:
                return jsonify({'message': f'Doctor is only available on {appt.doctor.availability}s'}), 400
        
        
        doc = appt.doctor
        if doc.time_availability and ' - ' in doc.time_availability:
            start_str, end_str = doc.time_availability.split(' - ')
            start_time = parse_time_logic(start_str)
            end_time = parse_time_logic(end_str)
            req_time = parse_time_logic(new_time_slot)
            
            if start_time and end_time and req_time:
                if not (start_time <= req_time <= end_time):
                    return jsonify({'message': f'Doctor is only available between {start_str} and {end_str}'}), 400
            elif not req_time:
                 return jsonify({'message': 'Invalid time format. Please use e.g. 10:00 AM'}), 400
        
        
        conflict = Appointment.query.filter(
            Appointment.doctor_id == appt.doctor_id,
            Appointment.date == parsed_date,
            Appointment.time_slot == new_time_slot,
            Appointment.id != appt.id,
            Appointment.status != 'Cancelled'
        ).first()

        if conflict:
            return jsonify({'message': 'Time slot already taken'}), 400
            
        appt.date = parsed_date
        appt.time_slot = new_time_slot
        appt.status = 'Booked' 
        
    db.session.commit()
    

    cache.delete(f"patient_history_{patient.id}")
    cache.delete(f"doctor_dashboard_{appt.doctor_id}")
    cache.delete("admin_dashboard_stats")
    print(f"\n[CACHE] Patient {patient.id} updated/cancelled an appointment. Parent/Doctor/Admin caches cleared.\n")
    
    return jsonify({'message': 'Appointment updated successfully.'}), 200

@app.route('/api/patient/history', methods=['GET'])
@patient_required
def get_patient_history_self():
    user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    cache_key = f"patient_history_{patient.id}"
    cached = cache.get(cache_key)
    if cached:
        print(f"\n[CACHE HIT] Patient {patient.id} history loaded instantly!\n")
        return jsonify(cached), 200
    
    results = []
    appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.desc()).all()
    
    for appt in appts:
        appt_data = {
            'id': appt.id,
            'doctor_name': appt.doctor.user.username,
            'specialization': appt.doctor.specialization,
            'date': str(appt.date),
            'time_slot': appt.time_slot,
            'status': appt.status,
            'treatment': None
        }
        
        if appt.treatment:
            appt_data['treatment'] = {
                'diagnosis': appt.treatment.diagnosis,
                'prescription': appt.treatment.prescription,
                'notes': appt.treatment.notes
            }
        results.append(appt_data)
    
    cache.set(cache_key, results, timeout=600) 
    return jsonify(results), 200

@app.route('/api/patient/<int:patient_id>/history', methods=['GET'])
@jwt_required()
def cross_role_patient_history(patient_id):
    claims = get_jwt()
    user_role = claims.get('role')
    user_id = int(get_jwt_identity())
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    has_access = False
    if user_role == 'Admin':
        has_access = True
    elif user_role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if Appointment.query.filter_by(doctor_id=doctor.id, patient_id=patient_id).first():
            has_access = True
    elif user_role == 'Patient':
        if patient.user_id == user_id:
            has_access = True
            
    if not has_access:
        return jsonify({'message': 'Access forbidden'}), 403
        
    history = []
    
    query = Appointment.query.filter_by(patient_id=patient.id)
    if user_role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        query = query.filter_by(doctor_id=doctor.id)
        
    appts = query.order_by(Appointment.date.desc()).all()
    
    for appt in appts:
        appt_data = {
            'id': appt.id,
            'date': str(appt.date),
            'time_slot': appt.time_slot,
            'doctor_name': appt.doctor.user.username,
            'specialization': appt.doctor.specialization,
            'status': appt.status,
            'treatment': None
        }
        if appt.treatment:
            appt_data['treatment'] = {
                'diagnosis': appt.treatment.diagnosis,
                'prescription': appt.treatment.prescription,
                'notes': appt.treatment.notes
            }
        history.append(appt_data)
        
    return jsonify({
        'patient_name': patient.user.username,
        'history': history
    }), 200

@app.route('/api/patient/export-history', methods=['POST'])
@patient_required
def trigger_export():
    from flask import send_file
    import io
    import csv
    
    user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date.desc()).all()
    
    #download medical history 
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Patient ID', 'Patient Name', 'Doctor', 'Appointment Date', 'Time Slot', 'Specialization', 'Diagnosis', 'Prescription', 'Next Visit/Notes', 'Status'])
    
    for appt in appts:
        diag = appt.treatment.diagnosis if appt.treatment else ""
        presc = appt.treatment.prescription if appt.treatment else ""
        notes = appt.treatment.notes if appt.treatment else ""
        
        writer.writerow([
            patient.user_id, patient.user.username, appt.doctor.user.username, 
            str(appt.date), appt.time_slot, appt.doctor.specialization, 
            diag, presc, notes, appt.status
        ])
        
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        download_name=f'Medical_History_{patient.user.username}.csv',
        as_attachment=True
    )

@app.route('/api/appointments/<int:appointment_id>/status', methods=['PATCH'])
@jwt_required()
def update_shared_appointment_status(appointment_id):
    claims = get_jwt()
    user_role = claims.get('role')
    user_id = int(get_jwt_identity())
    
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
        
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['Booked', 'Completed', 'Cancelled']:
        return jsonify({'message': 'Invalid status'}), 400

    has_access = False
    if user_role == 'Admin':
        has_access = True
    elif user_role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if appt.doctor_id == doctor.id:
            has_access = True
    elif user_role == 'Patient':
        patient = Patient.query.filter_by(user_id=user_id).first()
        if appt.patient_id == patient.id:
            if new_status == 'Cancelled':
                has_access = True
            else:
                return jsonify({'message': 'Patients can only Cancel appointments.'}), 403

    if not has_access:
        return jsonify({'message': 'Access cancelled'}), 403
        
    appt.status = new_status
    db.session.commit()
    
    cache.delete(f"patient_history_{appt.patient_id}")
    cache.delete(f"doctor_dashboard_{appt.doctor_id}")
    cache.delete("admin_dashboard_stats")
    
    return jsonify({'message': f'Appointment updated to {new_status}'}), 200


# CELERY & REDIS
@celery.task(name='app.send_daily_reminders')
def send_daily_reminders():
    
    from flask_mail import Message
    today = datetime.now().date()
    appointments = Appointment.query.filter_by(date=today, status='Booked').all()
    for appt in appointments:
        msg = Message(
            subject="Hospital Appointment Reminder",
            recipients=[appt.patient.user.email],
            body=f"Dear {appt.patient.user.username},\n\nYou have an appointment today at {appt.time_slot} with Dr. {appt.doctor.user.username}.\n\nPlease arrive on time.\n\nBest regards,\nHospital Management System"
        )
        mail.send(msg)
        print(f"[EMAIL] Reminder sent to {appt.patient.user.email}")
    return f"Sent {len(appointments)} email reminders."

@celery.task(name='app.generate_monthly_doctor_report')
def generate_monthly_doctor_report():

    from flask_mail import Message
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    
    doctors = Doctor.query.all()
    reports_generated = 0
    for doc in doctors:
        appts = Appointment.query.filter(
            Appointment.doctor_id == doc.id,
            Appointment.date >= start_of_month,
            Appointment.date <= today,
            Appointment.status == 'Completed'
        ).all()
        
        if not appts:
            continue
            
        html_report = f"<h1>Monthly Report for Dr. {doc.user.username}</h1>\n<ul>"
        for a in appts:
            diag = a.treatment.diagnosis if a.treatment else "No diagnosis"
            html_report += f"<li>{a.date}: Patient {a.patient.user.username} - {diag}</li>\n"
        html_report += "</ul>"
        
        msg = Message(
            subject="Monthly Activity Report",
            recipients=[doc.user.email],
            html=html_report
        )
        mail.send(msg)
        print(f"[EMAIL] Monthly report sent to Dr. {doc.user.email}")
        reports_generated += 1
        
    return f"Generated and emailed {reports_generated} monthly reports."

@celery.task(name='app.export_treatment_csv')
def export_treatment_csv(patient_id):
    from flask_mail import Message
    
    patient = Patient.query.get(patient_id)
    if not patient:
        print(f"[ERROR] Patient {patient_id} not found for export.")
        return
        
    appts = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.date.desc()).all()
    
    os.makedirs('exports', exist_ok=True)
    filename = f"exports/patient_{patient_id}_history_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Patient ID', 'Patient Name', 'Doctor', 'Appointment Date', 'Time Slot', 'Specialization', 'Diagnosis', 'Prescription', 'Next Visit/Notes', 'Status'])
        
        for appt in appts:
            diag = appt.treatment.diagnosis if appt.treatment else ""
            presc = appt.treatment.prescription if appt.treatment else ""
            notes = appt.treatment.notes if appt.treatment else ""
            
            writer.writerow([
                patient.user_id, patient.user.username, appt.doctor.user.username, 
                str(appt.date), appt.time_slot, appt.doctor.specialization, 
                diag, presc, notes, appt.status
            ])
            
    try:
        msg = Message(
            subject="Your Medical History Export (Async Alert)",
            recipients=[patient.user.email],
            body=f"Hello {patient.user.username},\n\nYour requested async batch job is complete! As requested, we have attached your full treatment history CSV report to this email.\n\nThank you,\nHospital Administration"
        )
        with app.app_context():
            with open(filename, "rb") as fp:
                msg.attach(f"medical_history_{patient_id}.csv", "text/csv", fp.read())
            mail.send(msg)
        print(f"\n[ALERT - JOB COMPLETE] CSV Export complete & Emailed to {patient.user.email}! File saved at {filename}\n")
    except Exception as e:
        print(f"\n[ALERT - JOB COMPLETE] CSV Export generated locally at {filename}, but email failed: {str(e)}\n")
        
    return filename


celery_app = celery 

if __name__ == '__main__':
    app.run(debug=True, port=5000)