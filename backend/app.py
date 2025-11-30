from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager
import os

from models import db, init_database
from controllers import (
    Authentication,
    DepartmentList,
    DepartmentDetail,
    AdminDoctors,
    AdminDoctorDetail,
    AdminPatients,
    DoctorAvailabilityResource,
    DoctorSlots,
    SearchDoctors,
    Appointments,
    AppointmentDetail,
    TreatmentResource,
    AdminDashboard,
    AdminAnalytics,
    DoctorDashboard,
    PatientDashboard,
    PatientProfileResource,
    DoctorPatientHistory,
    ExportTreatmentCSV,
    ExportTreatmentAsync,
    ExportJobStatus,
    send_export_file,
)

app = Flask(__name__)

# App settings and configs
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change_this_secret_in_prod")
db_path = os.getenv("SQLITE_PATH", "hms.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change_this_jwt_secret_in_prod")
app.config["JWT_IDENTITY_CLAIM"] = "sub"
app.config["JWT_ERROR_MESSAGE_KEY"] = "message"

# CORS 
frontend_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://localhost:5174")
CORS(app, resources={r"/api/*": {"origins": frontend_origins.split(",")}})

# Extensions
jwt = JWTManager(app)
db.init_app(app)

api = Api(app)

# Authentication endpoints
api.add_resource(Authentication, "/api/auth")

# Admin: Department endpoints
api.add_resource(DepartmentList, "/api/admin/departments")
api.add_resource(DepartmentDetail, "/api/admin/departments/<int:dept_id>")

# Admin: Doctors & Patients endpoints
api.add_resource(AdminDoctors, "/api/admin/doctors")
api.add_resource(AdminDoctorDetail, "/api/admin/doctors/<int:doctor_id>")
api.add_resource(AdminPatients, "/api/admin/patients", "/api/admin/patients/<int:patient_id>")

# Doctor availabilityendpoints
api.add_resource(DoctorAvailabilityResource, "/api/doctor/availability")

# Doctor slots (for patients)
api.add_resource(DoctorSlots, "/api/doctors/<int:doctor_id>/slots")

# Search Doctors 
api.add_resource(SearchDoctors, "/api/doctors/search")


api.add_resource(Appointments, "/api/appointments")
api.add_resource(AppointmentDetail, "/api/appointments/<int:appointment_id>")

# Treatment
api.add_resource(TreatmentResource, "/api/appointments/<int:appointment_id>/treatment")

# Dashboard endpoints
api.add_resource(AdminDashboard, "/api/admin/dashboard")
api.add_resource(AdminAnalytics, "/api/admin/analytics")
api.add_resource(DoctorDashboard, "/api/doctor/dashboard")
api.add_resource(PatientDashboard, "/api/patient/dashboard")

# Profiles & History of doctor and patient
api.add_resource(PatientProfileResource, "/api/patient/profile")
api.add_resource(DoctorPatientHistory, "/api/doctor/patients/<int:patient_id>/history")


api.add_resource(ExportTreatmentCSV, "/api/patient/export")
api.add_resource(ExportTreatmentAsync, "/api/patient/export/async")
api.add_resource(ExportJobStatus, "/api/patient/export/jobs/<int:job_id>")


# Download route for the exported file
@app.route("/api/download/<path:filename>")
def download_export(filename):
    return send_export_file(filename)


if __name__ == "__main__":
    with app.app_context():
        init_database()  # create tables, seed admin and default departments
    app.run(debug=True)
