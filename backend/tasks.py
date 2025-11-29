import os
import csv
from datetime import datetime, date, timedelta
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import traceback

from celery_app import celery
from app import app  
from models import (
    db,
    User,
    Department,
    DoctorProfile,
    PatientProfile,
    Appointment,
    Treatment,
    MonthlyReport,
    ExportJob,
)

# ============================================================================
# EMAIL CONFIGURATION - Customize these values
# ============================================================================
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SENDER_EMAIL = os.getenv("SMTP_FROM", "noreply@hospital.com")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASS", "")
# MailHog doesn't support STARTTLS, so default to false for localhost
SMTP_USE_STARTTLS = os.getenv("SMTP_STARTTLS", "false").lower() == "true"


def _send_email(
    subject: str,
    to_email: str,
    html_body: str,
    text_fallback: str = "",
    attachment_path: str | None = None,
):
    """
    Enhanced email helper with better attachment handling and error logging.
    - Reads SMTP settings from env or uses defaults
    - Falls back to console log if not configured
    - Can attach a single file if a path is provided
    - Uses MIMEMultipart for better compatibility
    """
    try:
        print(f"\n{'='*60}")
        print(f"📧 SENDING EMAIL")
        print(f"{'='*60}")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   SMTP Host: {SMTP_HOST}")
        print(f"   SMTP Port: {SMTP_PORT}")
        print(f"   Use STARTTLS: {SMTP_USE_STARTTLS}")
        print(f"   Has Auth: {bool(SMTP_USER and SMTP_PASSWORD)}")
        
        # If SMTP not configured, just log to console
        if not SMTP_HOST or SMTP_PORT == 0:
            print(f"   ⚠️ SMTP not configured - logging only")
            print(f"   Body preview: {html_body[:200]}...")
            print(f"{'='*60}\n")
            return False

        # Create message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        
        # Attach HTML body
        msg.attach(MIMEText(text_fallback or "Please view this email in HTML format.", "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            filename = os.path.basename(attachment_path)
            print(f"   📎 Attaching file: {filename}")
            
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)
            
            print(f"   ✅ Attachment added: {filename}")
        elif attachment_path:
            print(f"   ⚠️ Attachment file not found: {attachment_path}")

        # Send email
        print(f"   🔌 Connecting to SMTP server...")
        with smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT, timeout=10) as server:
            server.set_debuglevel(0)  # Set to 1 for verbose SMTP debugging
            
            if SMTP_USE_STARTTLS:
                print(f"   🔒 Starting TLS...")
                server.starttls()
            
            if SMTP_USER and SMTP_PASSWORD:
                print(f"   🔑 Logging in as {SMTP_USER}...")
                server.login(SMTP_USER, SMTP_PASSWORD)
            else:
                print(f"   ℹ️ No authentication (MailHog mode)")
            
            print(f"   📤 Sending message...")
            server.send_message(msg)
        
        print(f"   ✅ Email sent successfully to {to_email}")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Email failed: {e}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        return False


@celery.task(name="tasks.daily_reminders")
def daily_reminders():
    """Send beautiful daily appointment reminders to patients with appointments today."""
    with app.app_context():
        today = date.today()
        appts = Appointment.query.filter(
            Appointment.status == "Booked",
            Appointment.appointment_date == today
        ).all()

        sent_count = 0
        failed_count = 0
        
        for appt in appts:
            patient = PatientProfile.query.get(appt.patient_id)
            doctor = DoctorProfile.query.get(appt.doctor_id)
            
            if not patient or not doctor:
                failed_count += 1
                continue
                
            patient_user = patient.user
            doctor_user = doctor.user
            
            if not patient_user or not patient_user.email:
                failed_count += 1
                continue

            # Build beautiful HTML email
            subject = f"🏥 Appointment Reminder - Today at {appt.appointment_time.strftime('%I:%M %p')}"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px;">🏥 Appointment Reminder</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your appointment is scheduled for today</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 30px;">
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Dear <strong>{patient_user.name}</strong>,</p>
                        
                        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-left: 4px solid #2196f3; padding: 20px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">This is a friendly reminder about your appointment:</p>
                            <p style="margin: 10px 0; font-size: 20px; font-weight: bold; color: #1565c0;">
                                Today at {appt.appointment_time.strftime('%I:%M %p')}
                            </p>
                        </div>
                        
                        <!-- Appointment Details -->
                        <h2 style="font-size: 18px; color: #333; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #4caf50; padding-bottom: 10px;">
                            📋 Appointment Details
                        </h2>
                        
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <tr>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666; width: 40%;">Doctor:</td>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333; font-weight: bold;">Dr. {doctor_user.name if doctor_user else 'Doctor'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666;">Specialization:</td>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333;">{doctor.specialization if doctor else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666;">Date:</td>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333;">{appt.appointment_date.strftime('%A, %B %d, %Y')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666;">Time:</td>
                                <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333; font-weight: bold; font-size: 16px;">{appt.appointment_time.strftime('%I:%M %p')}</td>
                            </tr>
                            {f'<tr><td style="padding: 12px 0; color: #666;">Reason:</td><td style="padding: 12px 0; color: #333;">{appt.reason}</td></tr>' if appt.reason else ''}
                        </table>
                        
                        <!-- Important Reminders -->
                        <div style="background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #e65100;">⏰ Important Reminders:</h3>
                            <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 1.8;">
                                <li>Please arrive <strong>10-15 minutes early</strong></li>
                                <li>Bring your medical records and insurance information</li>
                                <li>Wear a mask if you have cold or flu symptoms</li>
                                <li>If you need to cancel, please notify us as soon as possible</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; color: #666; margin-top: 25px; line-height: 1.6;">
                            If you have any questions or need to reschedule, please contact our office.
                        </p>
                        
                        <p style="font-size: 14px; color: #666; margin-top: 15px;">
                            We look forward to seeing you!
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                        <p style="margin: 0; font-size: 12px; color: #999;">
                            © {datetime.now().year} Hospital Management System. All rights reserved.
                        </p>
                        <p style="margin: 5px 0 0 0; font-size: 11px; color: #bbb;">
                            This is an automated reminder. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_fallback = f"Appointment Reminder: You have an appointment today with Dr. {doctor_user.name if doctor_user else 'Doctor'} at {appt.appointment_time.strftime('%I:%M %p')}. Please arrive 10 minutes early."
            
            if _send_email(subject, patient_user.email, html, text_fallback):
                sent_count += 1
            else:
                failed_count += 1

        result_msg = f"[Daily Reminders] Sent {sent_count} reminders for {today.isoformat()}"
        if failed_count > 0:
            result_msg += f" ({failed_count} failed)"
        print(result_msg)
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "date": today.isoformat(),
            "total_appointments": len(appts)
        }


@celery.task(name="tasks.monthly_activity_report")
def monthly_activity_report():
    """
    Generate and email comprehensive monthly activity reports for each doctor.
    
    For TESTING: Uses current month's data (November 2025)
    For PRODUCTION: Uncomment the code below to use last month's data
    """
    with app.app_context():
        today = datetime.utcnow().date()
        first_of_this_month = today.replace(day=1)
        
        # ⚠️ TESTING MODE: Using CURRENT MONTH data
        # Change these lines for production use
        first_day_report_month = first_of_this_month
        last_day_report_month = today
        month_name = datetime.now().strftime('%B %Y')
        
        # PRODUCTION MODE (uncomment for real deployment):
        # last_month_end = first_of_this_month - timedelta(days=1)
        # first_day_report_month = last_month_end.replace(day=1)
        # last_day_report_month = last_month_end
        # month_name = last_month_end.strftime('%B %Y')

        doctors = DoctorProfile.query.all()
        generated = 0
        failed = 0

        exports_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(exports_dir, exist_ok=True)

        for doc in doctors:
            try:
                doctor_user = doc.user
                if not doctor_user or not doctor_user.email:
                    print(f"⚠️ Skipping doctor {doc.id} - no user or email")
                    failed += 1
                    continue

                # Get appointments for the report month
                appts = Appointment.query.filter(
                    Appointment.doctor_id == doc.id,
                    Appointment.appointment_date >= first_day_report_month,
                    Appointment.appointment_date <= last_day_report_month
                ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

                total = len(appts)
                
                # Skip doctors with no activity
                if total == 0:
                    print(f"⚠️ Skipping {doctor_user.email} - no appointments in {month_name}")
                    continue

                # Calculate statistics
                completed = sum(1 for a in appts if a.status == 'Completed')
                booked = sum(1 for a in appts if a.status == 'Booked')
                cancelled = sum(1 for a in appts if a.status == 'Cancelled')
                
                # Build appointments table HTML
                rows_html = ""
                for idx, a in enumerate(appts, 1):
                    patient_name = a.patient.user.name if a.patient and a.patient.user else 'N/A'
                    status_color = '#4caf50' if a.status == 'Completed' else '#ff9800' if a.status == 'Booked' else '#f44336'
                    row_bg = '#f8f9fa' if idx % 2 == 0 else 'white'
                    
                    rows_html += f"""
                    <tr style="background-color: {row_bg};">
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{idx}</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{a.appointment_date.strftime('%b %d, %Y')}</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{a.appointment_time.strftime('%I:%M %p')}</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{patient_name}</td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                            <span style="padding: 4px 8px; border-radius: 4px; background-color: {status_color}; color: white; font-size: 11px; font-weight: bold;">
                                {a.status.upper()}
                            </span>
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 12px; color: #666;">{a.reason or '-'}</td>
                    </tr>
                    """

                # Create beautiful HTML report
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
                    <div style="max-width: 800px; margin: 20px auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 32px;">📊 Monthly Activity Report</h1>
                            <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{month_name}</p>
                        </div>
                        
                        <!-- Content -->
                        <div style="padding: 30px;">
                            <p style="font-size: 16px; color: #333; margin-bottom: 10px;">Dear <strong>Dr. {doctor_user.name}</strong>,</p>
                            <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 25px;">
                                Here is your comprehensive activity summary for <strong>{month_name}</strong>. Thank you for your dedicated service!
                            </p>
                            
                            <!-- Statistics Grid -->
                            <h2 style="font-size: 20px; color: #667eea; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                                📈 Performance Metrics
                            </h2>
                            
                            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                                <tr>
                                    <td style="width: 25%; padding: 20px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-radius: 8px; text-align: center; margin-right: 10px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #1565c0;">{total}</div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">Total</div>
                                    </td>
                                    <td style="width: 25%; padding: 20px; background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-radius: 8px; text-align: center; margin: 0 5px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #2e7d32;">{completed}</div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">Completed</div>
                                    </td>
                                    <td style="width: 25%; padding: 20px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border-radius: 8px; text-align: center; margin: 0 5px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #e65100;">{booked}</div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">Booked</div>
                                    </td>
                                    <td style="width: 25%; padding: 20px; background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); border-radius: 8px; text-align: center; margin-left: 10px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #c62828;">{cancelled}</div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">Cancelled</div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Appointments Table -->
                            <h2 style="font-size: 20px; color: #667eea; margin-bottom: 20px; margin-top: 30px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                                📅 Detailed Appointments ({total})
                            </h2>
                            
                            <div style="overflow-x: auto;">
                                <table style="width: 100%; border-collapse: collapse; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                                    <thead>
                                        <tr style="background-color: #667eea; color: white;">
                                            <th style="padding: 12px; text-align: center; font-size: 13px; width: 5%;">#</th>
                                            <th style="padding: 12px; text-align: left; font-size: 13px; width: 15%;">Date</th>
                                            <th style="padding: 12px; text-align: left; font-size: 13px; width: 12%;">Time</th>
                                            <th style="padding: 12px; text-align: left; font-size: 13px; width: 20%;">Patient</th>
                                            <th style="padding: 12px; text-align: center; font-size: 13px; width: 13%;">Status</th>
                                            <th style="padding: 12px; text-align: left; font-size: 13px; width: 35%;">Reason</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows_html or '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #999;">No appointments</td></tr>'}
                                    </tbody>
                                </table>
                            </div>
                            
                            <!-- Thank You Section -->
                            <div style="background-color: #e8eaf6; padding: 20px; margin: 30px 0; border-radius: 8px; text-align: center;">
                                <h3 style="margin: 0 0 10px 0; font-size: 18px; color: #5e35b1;">🙏 Thank You for Your Service!</h3>
                                <p style="margin: 0; font-size: 14px; color: #666; line-height: 1.6;">
                                    Your dedication to patient care makes a real difference. We appreciate all your hard work!
                                </p>
                            </div>
                            
                            <p style="font-size: 14px; color: #666; margin-top: 25px;">
                                If you have any questions about this report, please contact the administration.
                            </p>
                        </div>
                        
                        <!-- Footer -->
                        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0; font-size: 12px; color: #999;">
                                © {datetime.now().year} Hospital Management System. All rights reserved.
                            </p>
                            <p style="margin: 5px 0 0 0; font-size: 11px; color: #bbb;">
                                Report generated on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')} UTC
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Save HTML report to file
                fname = f"doctor_{doc.id}_report_{first_day_report_month.year}_{first_day_report_month.month:02d}.html"
                fpath = os.path.join(exports_dir, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(html)

                # Record in MonthlyReport table
                rep = MonthlyReport.query.filter_by(
                    doctor_id=doc.id,
                    report_month=first_day_report_month.month,
                    report_year=first_day_report_month.year
                ).first()
                
                if not rep:
                    rep = MonthlyReport(
                        doctor_id=doc.id,
                        report_month=first_day_report_month.month,
                        report_year=first_day_report_month.year,
                        total_appointments=total,
                        generated_at=datetime.utcnow(),
                        file_path=fpath
                    )
                    db.session.add(rep)
                else:
                    rep.total_appointments = total
                    rep.generated_at = datetime.utcnow()
                    rep.file_path = fpath
                
                db.session.commit()

                # Email the report
                if _send_email(
                    subject=f"📊 Monthly Activity Report - {month_name}",
                    to_email=doctor_user.email,
                    html_body=html,
                    text_fallback=f"Your monthly activity report for {month_name} is ready. Total appointments: {total}"
                ):
                    rep.sent_at = datetime.utcnow()
                    db.session.commit()
                    generated += 1
                    print(f"✅ Report sent to {doctor_user.email} ({total} appointments)")
                else:
                    failed += 1
                    print(f"❌ Failed to send report to {doctor_user.email}")
                    
            except Exception as e:
                failed += 1
                print(f"❌ Error generating report for doctor {doc.id}: {e}")
                traceback.print_exc()
                db.session.rollback()

        result_msg = f"[Monthly Reports] Generated/emailed {generated} reports for {month_name}"
        if failed > 0:
            result_msg += f" ({failed} failed)"
        print(result_msg)
        
        return {
            "generated": generated,
            "failed": failed,
            "month": first_day_report_month.month,
            "year": first_day_report_month.year,
            "month_name": month_name
        }


@celery.task(name="tasks.export_patient_treatments")
def export_patient_treatments(user_id: int, job_id: int):
    """Async CSV export for patient's treatments (triggered by user customly according to needs)."""
    with app.app_context():
        job = ExportJob.query.get(job_id)
        if not job:
            return {"error": "Job not found"}

        try:
            job.status = "processing"
            db.session.commit()

            prof = PatientProfile.query.filter_by(user_id=user_id).first()
            if not prof:
                raise ValueError("Patient profile not found")

            rows = (
                db.session.query(
                    Appointment.id,
                    Appointment.appointment_date,
                    Appointment.appointment_time,
                    Treatment.diagnosis,
                    Treatment.prescription,
                    Treatment.notes,
                    Treatment.next_visit,
                    DoctorProfile.id.label("doctor_id"),
                    User.name.label("doctor_name"),
                    Department.name.label("department_name"),
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
                raise ValueError("No treatment/appointment records found")

            exports_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(exports_dir, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"patient_treatments_async_{user_id}_{ts}.csv"
            filepath = os.path.join(exports_dir, filename)

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Appointment ID",
                        "Date",
                        "Time",
                        "Doctor ID",
                        "Doctor Name",
                        "Department",
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
                            r[1].isoformat() if r[1] else "",
                            r[2].strftime("%H:%M") if r[2] else "",
                            r[7] or "",
                            r[8] or "",
                            r[9] or "",
                            r[3] or "",
                            r[4] or "",
                            r[5] or "",
                            r[6].isoformat() if r[6] else "",
                        ]
                    )

            job.status = "completed"
            job.file_path = filepath
            job.completed_at = datetime.utcnow()
            db.session.commit()

            #  email link to patient
            patient_user = prof.user
            if patient_user and patient_user.email:
                dl_url = f"http://localhost:5000/api/download/{filename}"
                
                subject = "📊 Your Treatment History Export is Ready"
                
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 20px auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <div style="background: linear-gradient(135deg, #2196f3 0%, #1565c0 100%); color: white; padding: 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 28px;">📊 View Your Reports</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your treatment history is ready to download</p>
                        </div>
                        
                        <!-- Content -->
                        <div style="padding: 30px;">
                            <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Dear <strong>{patient_user.name}</strong>,</p>
                            
                            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                <p style="margin: 0 0 10px 0; font-size: 16px; color: #2e7d32; font-weight: bold;">
                                    ✅ Your report has been successfully generated!
                                </p>
                                <p style="margin: 0; font-size: 14px; color: #666;">
                                    Your complete treatment history is now available for download as a CSV file.
                                </p>
                            </div>
                            
                            <!-- Export Details -->
                            <h2 style="font-size: 18px; color: #333; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #2196f3; padding-bottom: 10px;">
                                📋 Export Details
                            </h2>
                            
                            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666; width: 40%;">File Name:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333; font-family: monospace; font-size: 13px;">{filename}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666;">Generated:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333;">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #666;">Records:</td>
                                    <td style="padding: 12px 0; border-bottom: 1px solid #e0e0e0; color: #333; font-weight: bold;">{len(rows)} appointments</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #666;">Format:</td>
                                    <td style="padding: 12px 0; color: #333;">CSV (Comma Separated Values)</td>
                                </tr>
                            </table>
                            
                            <!-- Download Button -->
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{dl_url}" style="display: inline-block; background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                    ⬇️ Download CSV File
                                </a>
                            </div>
                            
                            <!-- Info Box -->
                            <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #1565c0;">📌 What's included:</h3>
                                <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 1.8;">
                                    <li>Appointment dates and times</li>
                                    <li>Doctor information and specializations</li>
                                    <li>Diagnoses and prescriptions</li>
                                    <li>Treatment notes and follow-up dates</li>
                                </ul>
                            </div>
                            
                            <p style="font-size: 14px; color: #666; margin-top: 25px; line-height: 1.6;">
                                You can open this file with Excel, Google Sheets, or any spreadsheet application. The file will remain available for download for the next 30 days.
                            </p>
                            
                            <p style="font-size: 14px; color: #666; margin-top: 15px;">
                                If you have any questions about your treatment history, please don't hesitate to contact us.
                            </p>
                        </div>
                        
                        <!-- Footer -->
                        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0; font-size: 12px; color: #999;">
                                © {datetime.now().year} Hospital Management System. All rights reserved.
                            </p>
                            <p style="margin: 5px 0 0 0; font-size: 11px; color: #bbb;">
                                This is an automated notification. Please do not reply to this email.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                text_fallback = f"Your treatment history export is ready. Download it here: {dl_url}"
                
                _send_email(subject, patient_user.email, html, text_fallback)

            return {"status": "completed", "file_path": filepath}

        except Exception as e:
            db.session.rollback()
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
            print(f"[Export ERROR] {e}")
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}


# ============================================================================
# TASK SCHEDULING CONFIGURATION
# ============================================================================
# 
# ⚠️ SCHEDULE TIMES ARE NOW CONFIGURED IN celery_app.py (lines 7-13)
# 
# To change when tasks run:
#   1. Edit times in celery_app.py
#   2. Delete schedule file: Remove-Item celerybeat-schedule*
#   3. Restart Celery Beat: celery -A celery_app beat --loglevel=info
# 
# Or run tasks manually without waiting:
#   python test_tasks.py
#
# ============================================================================


