from flask import request, send_from_directory
from flask_restful import Resource
from datetime import datetime, timedelta, date, time as time_cls
from functools import wraps
from sqlalchemy import and_, func, or_, case
from werkzeug.exceptions import BadRequest
from werkzeug.security import check_password_hash

from models import (
    db,
    User,
    Department,
    DoctorProfile,
    PatientProfile,
    DoctorAvailability,
    Appointment,
    Treatment,
    ExportJob,
)

from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)

try:
    from celery_app import celery
except Exception:
    celery = None

try:
    import os
    import redis

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

def get_current_user():
    """Helper to get current user_id and role from JWT"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")
    return {"user_id": int(user_id), "role": role}

#helpr functions for access according to roless
def require_roles(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            # pull identity and claims
            user_id = get_jwt_identity()
            claims = get_jwt()
            user_role = claims.get("role")
            
            if not user_id or not user_role:
                return {"message": "Unauthorized"}, 401
            if roles and user_role not in roles:
                return {"message": "Forbidden"}, 403
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def parse_time_str(hhmm: str) -> time_cls:
    """Accept 'HH:MM' and hand back a time object. Nothing fancy."""
    try:
        h, m = map(int, hhmm.split(":"))
        return time_cls(hour=h, minute=m)
    except Exception:
        # keep message stable; callers rely on it
        raise BadRequest("Invalid time format, expected HH:MM")


# ---------------------- for authentication ----------------------
class Authentication(Resource):
    def post(self):
        """Register a patient"""
        data = request.get_json() or {}
        for f in ["name", "email", "password"]:
            if not data.get(f):
                return {"message": f"Missing required field: {f}"}, 400
        email = data["email"].lower().strip()
        if User.query.filter_by(email=email).first():
            return {"message": "Email already registered"}, 400
        user = User(
            name=data["name"].strip(),
            email=email,
            role="patient",
            phone=data.get("phone"),
            address=data.get("address"),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()  # to get user.id

        # Create empty patient profile
        patient = PatientProfile(user_id=user.id)
        db.session.add(patient)
        db.session.commit()

        return {
            "message": "Registration successful",
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        }, 201

    def put(self):
        """Login (admin/doctor/patient)"""
        data = request.get_json() or {}
        email = data.get("email", "").lower().strip()
        password = data.get("password", "")

        if not email or not password:
            return {"message": "Email and password are required"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Invalid email or password"}, 401

        if not user.is_active:
            return {"message": "User is deactivated/blacklisted"}, 403

        user.last_login = datetime.utcnow()
        db.session.commit()

        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

        return {
            "message": "Login successful",
            "access_token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        }, 200


# ---------------------- Admin: Departments ----------------------
class DepartmentList(Resource):
    @require_roles("admin")
    def get(self):
        depts = Department.query.order_by(Department.name.asc()).all()
        return {"departments": [d.to_dict() for d in depts]}, 200

    @require_roles("admin")
    def post(self):
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        if not name:
            return {"message": "Department name is required"}, 400
        if Department.query.filter(func.lower(Department.name) == name.lower()).first():
            return {"message": "Department already exists"}, 400
        dept = Department(name=name, description=data.get("description"))
        db.session.add(dept)
        db.session.commit()
        return {"message": "Department created", "department": dept.to_dict()}, 201


class DepartmentDetail(Resource):
    @require_roles("admin")
    def put(self, dept_id):
        dept = Department.query.get(dept_id)
        if not dept:
            return {"message": "Department not found"}, 404
        data = request.get_json() or {}
        if "name" in data and data["name"].strip():
            dept.name = data["name"].strip()
        if "description" in data:
            dept.description = data["description"]
        db.session.commit()
        return {"message": "Department updated", "department": dept.to_dict()}, 200
    @require_roles("admin")
    def delete(self, dept_id):
        dept = Department.query.get(dept_id)
        if not dept:
            return {"message": "Department not found"}, 404
        db.session.delete(dept)
        db.session.commit()
        return {"message": "Department deleted"}, 200


# ---------------------- admins- doctors & patients ----------------------
class AdminDoctors(Resource):
    @require_roles("admin")
    def get(self):
        q = (request.args.get("q") or "").strip().lower()
        dept = (request.args.get("department") or "").strip()
        active = request.args.get("active")
        query = DoctorProfile.query.join(User, User.id == DoctorProfile.user_id)

        if active is not None:
            is_active = str(active).lower() in ["1", "true", "yes"]
            query = query.filter(DoctorProfile.is_active.is_(is_active), User.is_active.is_(is_active))

        if dept:
            query = query.join(Department, Department.id == DoctorProfile.department_id).filter(
                func.lower(Department.name).like(f"%{dept.lower()}%")
            )

        if q:
            query = query.filter(
                or_(
                    func.lower(User.name).like(f"%{q}%"),
                    func.lower(DoctorProfile.specialization).like(f"%{q}%"),
                    func.lower(User.email).like(f"%{q}%"),
                    func.lower(User.phone).like(f"%{q}%"),
                )
            )

        docs = query.all()
        return {"total": len(docs), "doctors": [d.to_public_dict() for d in docs]}, 200

    @require_roles("admin")
    def post(self):
        """Create a doctor user + profile"""
        data = request.get_json() or {}
        for f in ["name", "email", "password", "specialization"]:
            if not data.get(f):
                return {"message": f"Missing required field: {f}"}, 400

        email = data["email"].lower().strip()
        if User.query.filter_by(email=email).first():
            return {"message": "Email already registered"}, 400

        user = User(
            name=data["name"].strip(),
            email=email,
            role="doctor",
            phone=data.get("phone"),
            address=data.get("address"),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()

        dept_id = data.get("department_id")
        profile = DoctorProfile(
            user_id=user.id,
            specialization=data["specialization"].strip(),
            department_id=dept_id,
            bio=data.get("bio"),
            is_active=True,
        )
        db.session.add(profile)
        db.session.commit()

        return {"message": "Doctor created", "doctor": profile.to_public_dict()}, 201


class AdminDoctorDetail(Resource):
    @require_roles("admin")
    def put(self, doctor_id):
        profile = DoctorProfile.query.get(doctor_id)
        if not profile:
            return {"message": "Doctor not found"}, 404
        data = request.get_json() or {}

        if "specialization" in data and data["specialization"].strip():
            profile.specialization = data["specialization"].strip()
        if "department_id" in data:
            profile.department_id = data["department_id"]
        if "bio" in data:
            profile.bio = data["bio"]
        if "is_active" in data:
            profile.is_active = bool(data["is_active"])
            # Also update the user's active status
            if profile.user:
                profile.user.is_active = bool(data["is_active"])

        # Update user (name/phone/address) if present
        if profile.user:
            if "name" in data and data["name"].strip():
                profile.user.name = data["name"].strip()
            if "phone" in data:
                profile.user.phone = data["phone"]
            if "address" in data:
                profile.user.address = data["address"]

        db.session.commit()
        
        # Clear doctor search cache when doctor status changes
        if redis_client and "is_active" in data:
            try:
                # Clear all doctor search cache keys
                for key in redis_client.scan_iter("doc_search:*"):
                    redis_client.delete(key)
            except Exception:
                pass
        
        return {"message": "Doctor updated", "doctor": profile.to_public_dict()}, 200

    @require_roles("admin")
    def delete(self, doctor_id):
        """Blacklist/Deactivate doctor"""
        profile = DoctorProfile.query.get(doctor_id)
        if not profile:
            return {"message": "Doctor not found"}, 404
        profile.is_active = False
        if profile.user:
            profile.user.is_active = False
        db.session.commit()
        
        # Clear doctor search cache when doctor is deactivated
        if redis_client:
            try:
                for key in redis_client.scan_iter("doc_search:*"):
                    redis_client.delete(key)
            except Exception:
                pass
        
        return {"message": "Doctor deactivated"}, 200


class AdminPatients(Resource):
    @require_roles("admin")
    def get(self):
        q = (request.args.get("q") or "").strip().lower()
        active = request.args.get("active")

        query = PatientProfile.query.join(User, User.id == PatientProfile.user_id)

        if active is not None:
            is_active = str(active).lower() in ["1", "true", "yes"]
            query = query.filter(PatientProfile.is_active.is_(is_active), User.is_active.is_(is_active))

        if q:
            query = query.filter(
                or_(
                    func.lower(User.name).like(f"%{q}%"),
                    func.lower(User.email).like(f"%{q}%"),
                    func.lower(User.phone).like(f"%{q}%"),
                )
            )

        pats = query.all()
        out = [p.to_public_dict() for p in pats]
        return {"total": len(out), "patients": out}, 200

    @require_roles("admin")
    def put(self, patient_id):
        prof = PatientProfile.query.get(patient_id)
        if not prof:
            return {"message": "Patient not found"}, 404
        data = request.get_json() or {}
        if "dob" in data and data["dob"]:
            prof.dob = date.fromisoformat(data["dob"])
        if "gender" in data:
            prof.gender = data["gender"]
        if "emergency_contact" in data:
            prof.emergency_contact = data["emergency_contact"]
        if prof.user:
            if "name" in data and data["name"].strip():
                prof.user.name = data["name"].strip()
            if "phone" in data:
                prof.user.phone = data["phone"]
            if "address" in data:
                prof.user.address = data["address"]
            if "is_active" in data:
                prof.user.is_active = bool(data["is_active"])
        db.session.commit()
        return {"message": "Patient updated", "patient": prof.to_public_dict()}, 200

    @require_roles("admin")
    def delete(self, patient_id):
        prof = PatientProfile.query.get(patient_id)
        if not prof:
            return {"message": "Patient not found"}, 404
        if prof.user:
            prof.user.is_active = False
        prof.is_active = False
        db.session.commit()
        return {"message": "Patient deactivated"}, 200


#  Doctor Availability ----------------------
class DoctorAvailabilityResource(Resource):
    @require_roles("doctor")
    def get(self):
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404
        slots = DoctorAvailability.query.filter_by(doctor_id=doc.id).order_by(
            DoctorAvailability.available_date.asc(), DoctorAvailability.start_time.asc()
        ).all()
        return {"availability": [s.to_dict() for s in slots]}, 200

    @require_roles("doctor")
    def post(self):
        """Add availability slots. Payload: [{date:'YYYY-MM-DD', start:'HH:MM', end:'HH:MM'}, ...]"""
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404

        payload = request.get_json() or []
        if not isinstance(payload, list) or not payload:
            return {"message": "Provide a non-empty list of availability slots"}, 400

        created = []
        for item in payload:
            try:
                d = date.fromisoformat(item["date"])
                st = parse_time_str(item["start"])
                et = parse_time_str(item["end"])
                if et <= st:
                    return {"message": "end must be after start"}, 400
                slot = DoctorAvailability(
                    doctor_id=doc.id,
                    available_date=d,
                    start_time=st,
                    end_time=et,
                    fee=int(item["fee"]) if str(item.get("fee", "")).strip() != "" else None
                )
                db.session.add(slot)
                db.session.flush()
                created.append(slot.to_dict())
            except Exception as e:
                db.session.rollback()
                return {"message": f"Invalid slot entry: {str(e)}"}, 400

        db.session.commit()
        return {"message": "Availability added", "slots": created}, 201


# Doctor Slots (for patients) ----------------------
class DoctorSlots(Resource):
    @require_roles("patient", "admin")
    def get(self, doctor_id):
        """Get discrete 30-min bookable slots for a specific doctor (future only, excluding taken)."""
        doc = DoctorProfile.query.get(doctor_id)
        if not doc:
            return {"message": "Doctor not found"}, 404

        # Optional date filter (?date=YYYY-MM-DD)
        date_str = (request.args.get("date") or "").strip()
        target_date = None
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except Exception:
                return {"message": "Invalid date format, expected YYYY-MM-DD"}, 400

        today = date.today()
        # Availability windows for target date or future dates
        base_filter = [DoctorAvailability.doctor_id == doctor_id]
        if target_date:
            base_filter.append(DoctorAvailability.available_date == target_date)
        else:
            base_filter.append(DoctorAvailability.available_date >= today)

        avails = DoctorAvailability.query.filter(
            *base_filter
        ).order_by(
            DoctorAvailability.available_date.asc(),
            DoctorAvailability.start_time.asc()
        ).all()

        # Existing bookings (Booked or Completed) to exclude from free slots
        booked = db.session.query(
            Appointment.appointment_date, Appointment.appointment_time
        ).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= today,
            Appointment.status.in_(["Booked", "Completed"])
        ).all()
        booked_set = {(d, t) for (d, t) in booked}

        results = []
        for a in avails:
            # Build 30-min increments within [start, end)
            start_dt = datetime.combine(a.available_date, a.start_time)
            end_dt = datetime.combine(a.available_date, a.end_time)
            cur = start_dt
            while cur < end_dt:
                slot_date = a.available_date
                slot_time = cur.time()
                # Skip past times for today
                if slot_date == today and slot_time <= datetime.now().time():
                    cur += timedelta(minutes=30)
                    continue
                # Skip if an appointment already exists at this exact time
                if (slot_date, slot_time) not in booked_set:
                    next_dt = cur + timedelta(minutes=30)
                    # ensure end_time label does not exceed window end
                    end_label = (next_dt if next_dt <= end_dt else end_dt).time().strftime("%H:%M")
                    results.append({
                        "id": f"{slot_date.isoformat()}_{slot_time.strftime('%H:%M')}",
                        "doctor_id": doctor_id,
                        "available_date": slot_date.isoformat(),
                        "start_time": slot_time.strftime("%H:%M"),
                        "end_time": end_label,
                        "fee": a.fee
                    })
                cur += timedelta(minutes=30)

        return {"slots": results}, 200


# ---------------------- Search Doctors ----------------------
class SearchDoctors(Resource):
    def get(self):
        """Search doctors by specialization, department, name and optionally by date/time availability"""
        specialization = (request.args.get("specialization") or "").strip()
        dept = (request.args.get("department") or "").strip()
        name = (request.args.get("name") or "").strip()
        date_str = (request.args.get("date") or "").strip()
        time_str = (request.args.get("time") or "").strip()

        cache_key = None
        if redis_client:
            cache_key = f"doc_search:{specialization}:{dept}:{name}:{date_str}:{time_str}"
            cached = redis_client.get(cache_key)
            if cached:
                import json

                return json.loads(cached), 200

        q = DoctorProfile.query.join(User, DoctorProfile.user_id == User.id).filter(
            User.is_active.is_(True), DoctorProfile.is_active.is_(True)
        )

        if specialization:
            q = q.filter(func.lower(DoctorProfile.specialization).like(f"%{specialization.lower()}%"))
        if dept:
            q = q.join(Department, Department.id == DoctorProfile.department_id).filter(
                func.lower(Department.name).like(f"%{dept.lower()}%")
            )
        if name:
            q = q.filter(func.lower(User.name).like(f"%{name.lower()}%"))

        doctors = q.all()

        # If date/time provided, filter by availability
        if date_str:
            try:
                d = date.fromisoformat(date_str)
            except Exception:
                return {"message": "Invalid date format"}, 400

            if time_str:
                try:
                    t = parse_time_str(time_str)
                except BadRequest as e:
                    return {"message": str(e)}, 400

                result = []
                for doc in doctors:
                    has_slot = (
                        DoctorAvailability.query.filter(
                            DoctorAvailability.doctor_id == doc.id,
                            DoctorAvailability.available_date == d,
                            DoctorAvailability.start_time <= t,
                            DoctorAvailability.end_time > t,
                        ).first()
                        is not None
                    )
                    if has_slot:
                        result.append(doc.to_public_dict())
            else:
                result = [doc.to_public_dict() for doc in doctors if DoctorAvailability.query.filter_by(doctor_id=doc.id, available_date=d).first()]
        else:
            result = [doc.to_public_dict() for doc in doctors]

        response = {"total": len(result), "doctors": result}
        if redis_client and cache_key:
            import json

            redis_client.setex(cache_key, 300, json.dumps(response))  # cache 5 minutes

        return response, 200


# ---------------------- Appointments ----------------------
class Appointments(Resource):
    @require_roles("patient", "doctor", "admin")
    def get(self):
        """List appointments depending on role"""
        ident = get_current_user()
        role = ident["role"]
        user_id = ident["user_id"]

        # Check cache first
        cache_key = None
        if redis_client:
            cache_key = f"appointments:{role}:{user_id}"
            cached = redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached), 200

        q = Appointment.query

        if role == "patient":
            prof = PatientProfile.query.filter_by(user_id=user_id).first()
            if not prof:
                return {"message": "Patient profile not found"}, 404
            q = q.filter(Appointment.patient_id == prof.id)

        elif role == "doctor":
            prof = DoctorProfile.query.filter_by(user_id=user_id).first()
            if not prof:
                return {"message": "Doctor profile not found"}, 404
            q = q.filter(Appointment.doctor_id == prof.id)

        # admin sees all
        appts = q.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
        response = {"appointments": [a.to_dict() for a in appts]}
        
        # Cache the result for 2 minutes
        if redis_client and cache_key:
            import json
            redis_client.setex(cache_key, 120, json.dumps(response))
        
        return response, 200

    @require_roles("patient")
    def post(self):
        """Book an appointment. Payload: doctor_id, date(YYYY-MM-DD), time(HH:MM), reason"""
        ident = get_current_user()
        user_id = ident["user_id"]
        prof = PatientProfile.query.filter_by(user_id=user_id).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        data = request.get_json() or {}
        for f in ["doctor_id", "date", "time"]:
            if not data.get(f):
                return {"message": f"Missing required field: {f}"}, 400

        doc = DoctorProfile.query.get(data["doctor_id"])
        if not doc or not doc.is_active:
            return {"message": "Doctor not found/inactive"}, 404

        try:
            d = date.fromisoformat(data["date"])
            t = parse_time_str(data["time"])
        except Exception as e:
            return {"message": f"Invalid date/time: {e}"}, 400

        # Ensure doctor is available at that time window (exists an availability slot covering that time)
        avail = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doc.id,
            DoctorAvailability.available_date == d,
            DoctorAvailability.start_time <= t,
            DoctorAvailability.end_time > t,
        ).first()
        if not avail:
            return {"message": "Selected time not in doctor's availability"}, 409

        # Create appointment (DB UniqueConstraint is there so it prevents double booking for same doctor and slot)
        appt = Appointment(
            doctor_id=doc.id,
            patient_id=prof.id,
            appointment_date=d,
            appointment_time=t,
            reason=data.get("reason"),
            status="Booked",
        )
        db.session.add(appt)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "Time slot already booked for this doctor", "error": str(e)}, 409

        # Clear appointment cache for patient, doctor, and admin
        if redis_client:
            try:
                redis_client.delete(f"appointments:patient:{user_id}")
                redis_client.delete(f"appointments:doctor:{doc.user_id}")
                redis_client.delete(f"appointments:admin:*")
                # Clear all admin caches
                for key in redis_client.scan_iter("appointments:admin:*"):
                    redis_client.delete(key)
            except Exception:
                pass

        return {"message": "Appointment booked", "appointment": appt.to_dict()}, 201


class AppointmentDetail(Resource):
    @require_roles("patient", "admin", "doctor")
    def delete(self, appointment_id):
        """Cancel an appointment (patient or admin)"""
        ident = get_current_user()
        role = ident["role"]
        user_id = ident["user_id"]

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404

        if role == "patient":
            prof = PatientProfile.query.filter_by(user_id=user_id).first()
            if not prof or appt.patient_id != prof.id:
                return {"message": "Forbidden"}, 403
        elif role == "doctor":
            prof = DoctorProfile.query.filter_by(user_id=user_id).first()
            if not prof or appt.doctor_id != prof.id:
                return {"message": "Forbidden"}, 403

        if appt.status == "Cancelled":
            return {"message": "Already cancelled"}, 200

        appt.status = "Cancelled"
        db.session.commit()
        
        # Clear appointment cache for affected users
        if redis_client:
            try:
                # Clear patient cache
                patient = PatientProfile.query.get(appt.patient_id)
                if patient:
                    redis_client.delete(f"appointments:patient:{patient.user_id}")
                # Clear doctor cache
                doctor = DoctorProfile.query.get(appt.doctor_id)
                if doctor:
                    redis_client.delete(f"appointments:doctor:{doctor.user_id}")
                # Clear all admin caches
                for key in redis_client.scan_iter("appointments:admin:*"):
                    redis_client.delete(key)
            except Exception:
                pass
        
        return {"message": "Appointment cancelled"}, 200

    @require_roles("patient")
    def patch(self, appointment_id):
        """Reschedule appointment (only if still Booked)"""
        ident = get_current_user()
        prof = PatientProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        appt = Appointment.query.get(appointment_id)
        if not appt or appt.patient_id != prof.id:
            return {"message": "Appointment not found"}, 404

        if appt.status != "Booked":
            return {"message": "Only Booked appointments can be rescheduled"}, 400

        data = request.get_json() or {}
        if not data.get("date") or not data.get("time"):
            return {"message": "date and time required"}, 400

        try:
            d = date.fromisoformat(data["date"])
            t = parse_time_str(data["time"])
        except Exception as e:
            return {"message": f"Invalid date/time: {e}"}, 400

        # Check availability
        avail = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == appt.doctor_id,
            DoctorAvailability.available_date == d,
            DoctorAvailability.start_time <= t,
            DoctorAvailability.end_time > t,
        ).first()
        if not avail:
            return {"message": "Selected time not in doctor's availability"}, 409

        appt.appointment_date = d
        appt.appointment_time = t

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "Time slot already booked for this doctor", "error": str(e)}, 409

        # Clear appointment cache for patient, doctor, and admin
        if redis_client:
            try:
                redis_client.delete(f"appointments:patient:{ident['user_id']}")
                doctor = DoctorProfile.query.get(appt.doctor_id)
                if doctor:
                    redis_client.delete(f"appointments:doctor:{doctor.user_id}")
                # Clear all admin caches
                for key in redis_client.scan_iter("appointments:admin:*"):
                    redis_client.delete(key)
            except Exception:
                pass

        return {"message": "Appointment rescheduled", "appointment": appt.to_dict()}, 200


# -- Treatments (Doctor) ----------------------
class TreatmentResource(Resource):
    @require_roles("doctor", "patient")
    def get(self, appointment_id):
        """Fetch treatment details for an appointment (doctor or patient with access)."""
        ident = get_current_user()
        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Treatment not found"}, 404

        role = ident["role"]
        if role == "doctor":
            doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
            if not doc or appt.doctor_id != doc.id:
                return {"message": "Forbidden"}, 403
        elif role == "patient":
            pat = PatientProfile.query.filter_by(user_id=ident["user_id"]).first()
            if not pat or appt.patient_id != pat.id:
                return {"message": "Forbidden"}, 403

        if not appt.treatment:
            return {"message": "Treatment not found"}, 404

        return {"treatment": appt.treatment.to_dict()}, 200

    @require_roles("doctor")
    def post(self, appointment_id):
        """Mark as completed with treatment details"""
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404

        appt = Appointment.query.get(appointment_id)
        if not appt or appt.doctor_id != doc.id:
            return {"message": "Appointment not found"}, 404
        if appt.status == "Cancelled":
            return {"message": "Cannot complete a cancelled appointment"}, 400

        data = request.get_json() or {}
        if not data.get("diagnosis"):
            return {"message": "diagnosis is required"}, 400

        # Create or update treatment
        if appt.treatment:
            tr = appt.treatment
            tr.diagnosis = data.get("diagnosis")
            tr.prescription = data.get("prescription")
            tr.notes = data.get("notes")
            tr.next_visit = date.fromisoformat(data["next_visit"]) if data.get("next_visit") else None
        else:
            tr = Treatment(
                appointment_id=appt.id,
                diagnosis=data.get("diagnosis"),
                prescription=data.get("prescription"),
                notes=data.get("notes"),
                next_visit=date.fromisoformat(data["next_visit"]) if data.get("next_visit") else None,
            )
            db.session.add(tr)

        appt.status = "Completed"
        db.session.commit()
        
        # Clear appointment cache for patient, doctor, and admin
        if redis_client:
            try:
                patient = PatientProfile.query.get(appt.patient_id)
                if patient:
                    redis_client.delete(f"appointments:patient:{patient.user_id}")
                redis_client.delete(f"appointments:doctor:{ident['user_id']}")
                # Clear all admin caches
                for key in redis_client.scan_iter("appointments:admin:*"):
                    redis_client.delete(key)
            except Exception:
                pass
        
        return {"message": "Treatment saved and appointment marked Completed", "treatment": tr.to_dict()}, 200

    @require_roles("doctor")
    def put(self, appointment_id):
        """Update treatment notes (if already exists)"""
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404

        appt = Appointment.query.get(appointment_id)
        if not appt or appt.doctor_id != doc.id or not appt.treatment:
            return {"message": "Treatment not found"}, 404

        data = request.get_json() or {}
        for f in ["diagnosis", "prescription", "notes"]:
            if f in data:
                setattr(appt.treatment, f, data[f])
        if "next_visit" in data:
            appt.treatment.next_visit = date.fromisoformat(data["next_visit"]) if data["next_visit"] else None

        db.session.commit()
        return {"message": "Treatment updated", "treatment": appt.treatment.to_dict()}, 200


# ---------------------- Dashboards ----------------------
class AdminDashboard(Resource):
    @require_roles("admin")
    def get(self):
        total_doctors = DoctorProfile.query.count()
        total_patients = PatientProfile.query.count()
        total_appointments = Appointment.query.count()

        upcoming = Appointment.query.filter(
            and_(Appointment.status == "Booked", Appointment.appointment_date >= date.today())
        ).count()

        completed = Appointment.query.filter_by(status="Completed").count()
        cancelled = Appointment.query.filter_by(status="Cancelled").count()

        # search support metrics
        specializations = db.session.query(DoctorProfile.specialization, func.count(DoctorProfile.id)).group_by(
            DoctorProfile.specialization
        ).all()

        return {
            "overview": {
                "doctors": total_doctors,
                "patients": total_patients,
                "appointments": total_appointments,
                "upcoming": upcoming,
                "completed": completed,
                "cancelled": cancelled,
            },
            "specializations": [{"name": s[0], "count": s[1]} for s in specializations],
        }, 200


class AdminAnalytics(Resource):
    @require_roles("admin")
    def get(self):
        # Optional range (e.g., ?range=30d). Defaults to full history.
        rng = (request.args.get("range") or "").strip()
        days = None
        if rng.endswith("d"):
            try:
                days = int(rng[:-1])
            except Exception:
                days = None

        date_from = None
        if days and days > 0:
            date_from = date.today() + timedelta(days=0) - timedelta(days=days)

        filters = []
        if date_from:
            filters.append(Appointment.appointment_date >= date_from)

        # Top doctors by total appointments (booked,completed,cancelled) in range
        top_docs_rows = (
            db.session.query(
                DoctorProfile.id.label("doctor_id"),
                User.name.label("doctor_name"),
                func.count(Appointment.id).label("bookings"),
            )
            .join(User, User.id == DoctorProfile.user_id)
            .join(Appointment, Appointment.doctor_id == DoctorProfile.id)
            .filter(*filters)
            .group_by(DoctorProfile.id, User.name)
            .order_by(func.count(Appointment.id).desc())
            .limit(5)
            .all()
        )
        top_doctors = [
            {"doctor_id": r.doctor_id, "doctor_name": r.doctor_name, "bookings": int(r.bookings)}
            for r in top_docs_rows
        ]

        # Appointments by department in range
        appt_by_dept_rows = (
            db.session.query(
                Department.name.label("department"),
                func.count(Appointment.id).label("appointments"),
            )
            .join(DoctorProfile, DoctorProfile.id == Appointment.doctor_id)
            .join(Department, Department.id == DoctorProfile.department_id, isouter=True)
            .filter(*filters)
            .group_by(Department.name)
            .order_by(func.count(Appointment.id).desc())
            .all()
        )
        appointments_by_department = [
            {"department": (r.department or "Unassigned"), "appointments": int(r.appointments)}
            for r in appt_by_dept_rows
        ]

        # Revenue by department from completed visits: sum the fee of the availability window used
        revenue_by_dept_rows = (
            db.session.query(
                Department.name.label("department"),
                func.coalesce(func.sum(DoctorAvailability.fee), 0).label("value"),
            )
            .select_from(Appointment)
            .join(DoctorProfile, DoctorProfile.id == Appointment.doctor_id)
            .join(Department, Department.id == DoctorProfile.department_id, isouter=True)
            .join(
                DoctorAvailability,
                and_(
                    DoctorAvailability.doctor_id == Appointment.doctor_id,
                    DoctorAvailability.available_date == Appointment.appointment_date,
                    DoctorAvailability.start_time <= Appointment.appointment_time,
                    DoctorAvailability.end_time > Appointment.appointment_time,
                ),
                isouter=True,
            )
            .filter(Appointment.status == "Completed", *filters)
            .group_by(Department.name)
            .order_by(func.coalesce(func.sum(DoctorAvailability.fee), 0).desc())
            .all()
        )
        revenue_by_department = [
            {"department": (r.department or "Unassigned"), "value": int(r.value or 0)}
            for r in revenue_by_dept_rows
        ]

        return {
            "range_days": days,
            "top_doctors": top_doctors,
            "appointments_by_department": appointments_by_department,
            "revenue_by_department": revenue_by_department,
        }, 200

class DoctorDashboard(Resource):
    @require_roles("doctor")
    def get(self):
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404

        today = date.today()
        week_end = today + timedelta(days=7)

        todays_appts = Appointment.query.filter(
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date == today,
            Appointment.status == "Booked",
        ).order_by(Appointment.appointment_time.asc()).all()

        weeks_appts = Appointment.query.filter(
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= week_end,
        ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

        # list of patients assigned
        patient_ids = {a.patient_id for a in weeks_appts}
        patients = PatientProfile.query.filter(PatientProfile.id.in_(patient_ids)).all()

        return {
            "today": [a.to_dict() for a in todays_appts],
            "week": [a.to_dict() for a in weeks_appts],
            "patients": [p.to_public_dict() for p in patients],
        }, 200


class PatientDashboard(Resource):
    @require_roles("patient")
    def get(self):
        ident = get_current_user()
        prof = PatientProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        # Departments and specializations
        depts = [d.to_dict() for d in Department.query.order_by(Department.name.asc()).all()]

        # doctor's availability for next 7 days
        today = date.today()
        week_end = today + timedelta(days=7)
        upcoming_slots = DoctorAvailability.query.filter(
            DoctorAvailability.available_date >= today, DoctorAvailability.available_date <= week_end
        ).order_by(DoctorAvailability.available_date.asc(), DoctorAvailability.start_time.asc()).all()

        # upcoming and history
        upcoming_appts = Appointment.query.filter(
            Appointment.patient_id == prof.id,
            Appointment.status == "Booked",
        ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

        history = Appointment.query.filter(
            Appointment.patient_id == prof.id, Appointment.status.in_(["Completed", "Cancelled"])
        ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).limit(20).all()

        return {
            "departments": depts,
            "availability_next_week": [s.to_dict() for s in upcoming_slots],
            "upcoming_appointments": [a.to_dict() for a in upcoming_appts],
            "history": [a.to_dict() for a in history],
        }, 200


# ---------------------- Patient Profile (self) ----------------------
class PatientProfileResource(Resource):
    @require_roles("patient")
    def get(self):
        ident = get_current_user()
        prof = PatientProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        data = prof.to_public_dict()
        if prof.user:
            data["address"] = prof.user.address
        return {"profile": data}, 200

    @require_roles("patient")
    def put(self):
        """Update own profile fields"""
        ident = get_current_user()
        prof = PatientProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        data = request.get_json() or {}
        # Update patient profile fields
        if "dob" in data and data["dob"]:
            try:
                prof.dob = date.fromisoformat(data["dob"])
            except Exception:
                return {"message": "Invalid dob format, expected YYYY-MM-DD"}, 400
        if "gender" in data:
            prof.gender = data["gender"]
        if "emergency_contact" in data:
            prof.emergency_contact = data["emergency_contact"]

        # Update user fields
        if prof.user:
            if "name" in data and str(data["name"]).strip():
                prof.user.name = str(data["name"]).strip()
            if "phone" in data:
                prof.user.phone = data["phone"]
            if "address" in data:
                prof.user.address = data["address"]

        db.session.commit()
        return {"message": "Profile updated", "profile": prof.to_public_dict()}, 200


# ---------------------- Doctor: Patient History ----------------------
class DoctorPatientHistory(Resource):
    @require_roles("doctor")
    def get(self, patient_id: int):
        """Return full history between this doctor and the specified patient"""
        ident = get_current_user()
        doc = DoctorProfile.query.filter_by(user_id=ident["user_id"]).first()
        if not doc:
            return {"message": "Doctor profile not found"}, 404

        patient = PatientProfile.query.get(patient_id)
        if not patient:
            return {"message": "Patient not found"}, 404

        appts = (
            Appointment.query.filter(
                Appointment.doctor_id == doc.id,
                Appointment.patient_id == patient_id,
            )
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .all()
        )

        out = []
        for a in appts:
            item = a.to_dict()
            if a.treatment:
                item["treatment"] = a.treatment.to_dict()
            out.append(item)
        return {"patient": patient.to_public_dict(), "appointments": out}, 200

# ---------------------- Export CSV (patient) -----------------
import csv, os


class ExportTreatmentCSV(Resource):
    @require_roles("patient")
    def post(self):
        """User-triggered export (synchronous CSV generation). For async, wire this to a Celery task."""
        ident = get_current_user()
        user_id = ident["user_id"]
        prof = PatientProfile.query.filter_by(user_id=user_id).first()
        if not prof:
            return {"message": "Patient profile not found"}, 404

        # Collect treatments
        rows = (
            db.session.query(
                Appointment.id,
                User.name.label("patient_name"),
                func.coalesce(User.email, "").label("patient_email"),
                func.coalesce(func.coalesce(Department.name, DoctorProfile.specialization), "").label("department"),
                func.coalesce(func.coalesce(User.name, ""), "").label("doctor_name"),
                Appointment.appointment_date,
                Appointment.appointment_time,
                Treatment.diagnosis,
                Treatment.prescription,
                Treatment.notes,
                Treatment.next_visit,
            )
            .join(Treatment, Treatment.appointment_id == Appointment.id, isouter=True)
            .join(DoctorProfile, DoctorProfile.id == Appointment.doctor_id)
            .join(User, User.id == DoctorProfile.user_id)
            .join(Department, Department.id == DoctorProfile.department_id, isouter=True)
            .filter(Appointment.patient_id == prof.id)
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .all()
        )

        if not rows:
            return {"message": "No treatment/appointment records found"}, 404

        # ensure exports directory
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patient_treatments_{user_id}_{ts}.csv"
        filepath = os.path.join(export_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Appointment ID",
                    "Patient Name",
                    "Patient Email",
                    "Department/Specialization",
                    "Doctor Name",
                    "Appointment Date",
                    "Appointment Time",
                    "Diagnosis",
                    "Prescription",
                    "Notes",
                    "Next Visit",
                ]
            )
            for r in rows:
                writer.writerow(
                    [
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        r[4],
                        r[5].isoformat() if r[5] else "",
                        r[6].strftime("%H:%M") if r[6] else "",
                        r[7] or "",
                        r[8] or "",
                        r[9] or "",
                        r[10].isoformat() if r[10] else "",
                    ]
                )

        # Optionally persist job record
        job = ExportJob(user_id=user_id, job_type="patient_treatments_csv", status="completed", file_path=filepath)
        db.session.add(job)
        db.session.commit()

        return {
            "message": "Export completed",
            "filename": filename,
            "download_url": f"/api/download/{filename}",
            "total_records": len(rows),
        }, 200


# ----------------------downloading the patients consultation report ----------------------
def send_export_file(filename: str):
    export_dir = os.path.join(os.getcwd(), "exports")
    return send_from_directory(export_dir, filename, as_attachment=True)


# ---------------------- for csv  Exports ----------------------
class ExportTreatmentAsync(Resource):
    @require_roles("patient")
    def post(self):
        """Trigger async CSV export of patient's treatments via Celery"""
        ident = get_current_user()
        user_id = ident["user_id"]

        job = ExportJob(user_id=user_id, job_type="patient_treatments_csv", status="pending")
        db.session.add(job)
        db.session.commit()

        # trigger celery task without importing tasks module (avoid circular import)
        if celery is None:
            return {"message": "Async processing not available on this server"}, 503
        celery.send_task("tasks.export_patient_treatments", args=[user_id, job.id])

        return {"message": "Export started", "job_id": job.id}, 202


class ExportJobStatus(Resource):
    @require_roles("patient", "admin")
    def get(self, job_id: int):
        job = ExportJob.query.get(job_id)
        if not job:
            return {"message": "Job not found"}, 404
        return {"job": job.to_dict()}, 200
