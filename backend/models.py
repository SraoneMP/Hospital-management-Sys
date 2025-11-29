from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import UniqueConstraint, event, text

db = SQLAlchemy()

# Users and profiles (kept straightforward)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # admin | doctor | patient
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relations
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    patient_profile = db.relationship('PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    export_jobs = db.relationship('ExportJob', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, raw: str):
        self.password = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password, raw)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_doctor(self) -> bool:
        return self.role == 'doctor'

    def is_patient(self) -> bool:
        return self.role == 'patient'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Relations
    doctors = db.relationship('DoctorProfile', backref='department', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'doctors_registered': len(self.doctors)
        }

    def __repr__(self):
        return f'<Department {self.name}>'


class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    specialization = db.Column(db.String(120), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relations
    availabilities = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')

    def to_public_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else None,
            'specialization': self.specialization,
            'department': self.department.name if self.department else None,
            'bio': self.bio,
            'phone': self.user.phone if self.user else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<DoctorProfile {self.user.email if self.user else self.id}>'


class PatientProfile(db.Model):
    __tablename__ = 'patient_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # male | female | other
    emergency_contact = db.Column(db.String(50), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)


    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')

    def to_public_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.user.name if self.user else None,
            'email': self.user.email if self.user else None,
            'phone': self.user.phone if self.user else None,
            'dob': self.dob.isoformat() if self.dob else None,
            'gender': self.gender,
            'emergency_contact': self.emergency_contact,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<PatientProfile {self.user.email if self.user else self.id}>'

# Scheduling and medical records
class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profile.id'), nullable=False, index=True)
    available_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)  # e.g., 09:00
    end_time = db.Column(db.Time, nullable=False)    # e.g., 17:00
    fee = db.Column(db.Integer, nullable=True)       # fee for consulting

    __table_args__ = (
        UniqueConstraint('doctor_id', 'available_date', 'start_time', 'end_time', name='uq_doctor_availability_slot'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'available_date': self.available_date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'fee': self.fee
        }


class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profile.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profile.id'), nullable=False, index=True)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='Booked')  # Booked | Completed | Cancelled
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Prevent multiple appointments at the same date and time for the same doctor
    __table_args__ = (
        UniqueConstraint('doctor_id', 'appointment_date', 'appointment_time', name='uq_doctor_timeslot'),
    )

    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        result = {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.user.name if self.doctor and self.doctor.user else None,
            'patient_id': self.patient_id,
            'patient_name': self.patient.user.name if self.patient and self.patient.user else None,
            'appointment_date': self.appointment_date.isoformat(),
            'appointment_time': self.appointment_time.strftime('%H:%M'),
            'status': self.status,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        # Include treatment if exists
        if self.treatment:
            result['treatment'] = self.treatment.to_dict()
        return result


class Treatment(db.Model):
    __tablename__ = 'treatment'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, unique=True, index=True)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    next_visit = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'notes': self.notes,
            'next_visit': self.next_visit.isoformat() if self.next_visit else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Monthly reports and CSV export jobs
class MonthlyReport(db.Model):
    __tablename__ = 'monthly_report'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profile.id'), nullable=False, index=True)
    report_month = db.Column(db.Integer, nullable=False)
    report_year = db.Column(db.Integer, nullable=False)
    total_appointments = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.user.name if getattr(self, 'doctor', None) and self.doctor.user else None,
            'report_month': self.report_month,
            'report_year': self.report_year,
            'total_appointments': self.total_appointments,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'file_path': self.file_path
        }


class ExportJob(db.Model):
    __tablename__ = 'export_job'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # patient user triggering export
    job_type = db.Column(db.String(50), nullable=False, default='patient_treatments_csv')
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending | processing | completed | failed
    file_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_type': self.job_type,
            'status': self.status,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


# Database setup and a bit of seeding
def ensure_availability_fee_column():
    """If the fee column is missing on doctor_availability, add it (SQLite ALTER)."""
    try:
        conn = db.engine.connect()
        rows = conn.execute(text("PRAGMA table_info(doctor_availability)")).fetchall()
        cols = [r[1] for r in rows]
        if "fee" not in cols:
            conn.execute(text("ALTER TABLE doctor_availability ADD COLUMN fee INTEGER"))
    except Exception as e:
        print(f"[schema] fee column ensure failed: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

def create_default_departments():
    """Drop in a few usual departments if the table looks empty."""
    defaults = [
        ('Cardiology', 'Heart and cardiovascular care'),
        ('Dermatology', 'Skin-related diagnosis and treatment'),
        ('Neurology', 'Nervous system and brain'),
        ('Orthopedics', 'Bones and joints'),
        ('Pediatrics', 'Child health care'),
        ('General Medicine', 'Primary care and general practice'),
    ]
    existing = {d.name for d in Department.query.all()}
    for name, desc in defaults:
        if name not in existing:
            db.session.add(Department(name=name, description=desc))
    db.session.commit()


def create_admin_user():
    """Create a single admin if we don't already have one."""
    admin_email = 'admin@hospital.local'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name='System Administrator',
            email=admin_email,
            role='admin',
            phone='9999999999',
            address='Admin Office'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user created: {admin_email} / admin123')
    return admin


def init_database():
    """Create tables once, then seed admin and a few departments."""
    db.create_all()
    ensure_availability_fee_column()
    create_admin_user()
    create_default_departments()
    print('Hospital tables ready. Defaults seeded.')


# Optional: keep times consistent as python time objects on insert
@event.listens_for(DoctorAvailability, "before_insert")
def _validate_availability(mapper, connection, target: DoctorAvailability):
    if target.end_time <= target.start_time:
        raise ValueError("Availability end_time must be after start_time")
