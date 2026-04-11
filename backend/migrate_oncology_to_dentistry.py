from app import app, db
from models import Department, Doctor

def migrate():
    with app.app_context():
        # 1. Update Department name
        dept = Department.query.filter_by(name='Oncology').first()
        if dept:
            print(f"Updating Department: {dept.name} -> Dentistry")
            dept.name = 'Dentistry'
        else:
            print("Department 'Oncology' not found.")

        # 2. Update Doctor specializations
        doctors = Doctor.query.filter_by(specialization='Oncology').all()
        for doc in doctors:
            print(f"Updating Doctor {doc.user.username} specialization: {doc.specialization} -> Dentistry")
            doc.specialization = 'Dentistry'
        
        # 3. Check for 'Dentist' as well just in case
        doctors_dentist = Doctor.query.filter_by(specialization='Dentist').all()
        for doc in doctors_dentist:
            print(f"Updating Doctor {doc.user.username} specialization: {doc.specialization} -> Dentistry")
            doc.specialization = 'Dentistry'

        db.session.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
