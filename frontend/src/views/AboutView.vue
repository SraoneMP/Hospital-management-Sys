<template>
  <div class="about-page">
    <div class="container py-5">
      <!-- Header Section -->
      <div class="text-center mb-5">
        <h1 class="about-title">About Our Hospital Management System</h1>
        <p class="about-subtitle">Transforming Healthcare Through Technology</p>
      </div>

      <!-- Main Content -->
      <div class="row g-4">
        <!-- What We Do -->
        <div class="col-12">
          <div class="card info-card">
            <div class="card-body">
              <div class="d-flex align-items-center mb-3">
                <div class="icon-circle">🏥</div>
                <h2 class="section-title mb-0">What We Do</h2>
              </div>
              <p class="info-text">
                Our Hospital Management System is a comprehensive digital platform designed to streamline healthcare services 
                and enhance patient care. This application helps you manage all aspects of hospital operations efficiently, 
                from patient appointments to medical records, making healthcare more accessible and organized.
              </p>
            </div>
          </div>
        </div>

        <!-- Key Features -->
        <div class="col-12">
          <div class="card info-card">
            <div class="card-body">
              <div class="d-flex align-items-center mb-3">
                <div class="icon-circle">✨</div>
                <h2 class="section-title mb-0">Key Features</h2>
              </div>
              <div class="row g-3">
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">📅</div>
                    <div>
                      <h5 class="feature-title">Easy Appointment Booking</h5>
                      <p class="feature-text">Schedule appointments with doctors across multiple departments at your convenience.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">👨‍⚕️</div>
                    <div>
                      <h5 class="feature-title">Find Specialized Doctors</h5>
                      <p class="feature-text">Search and connect with expert doctors by specialization and department.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">📋</div>
                    <div>
                      <h5 class="feature-title">Medical Records Management</h5>
                      <p class="feature-text">Access your complete treatment history, prescriptions, and diagnoses anytime.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div>
                      <h5 class="feature-title">Export Your Data</h5>
                      <p class="feature-text">Download your medical records as CSV files for easy sharing and backup.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">🔔</div>
                    <div>
                      <h5 class="feature-title">Automated Reminders</h5>
                      <p class="feature-text">Receive email notifications for upcoming appointments and follow-ups.</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="feature-item">
                    <div class="feature-icon">🏢</div>
                    <div>
                      <h5 class="feature-title">Department Overview</h5>
                      <p class="feature-text">Browse available specializations and departments with registered doctors.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Who Can Use This -->
        <div class="col-12">
          <div class="card info-card">
            <div class="card-body">
              <div class="d-flex align-items-center mb-3">
                <div class="icon-circle">👥</div>
                <h2 class="section-title mb-0">Who Can Use This</h2>
              </div>
              <div class="row g-3">
                <div class="col-md-4">
                  <div class="user-role-card">
                    <div class="role-icon">🧑‍💼</div>
                    <h5 class="role-title">Administrators</h5>
                    <p class="role-text">Manage departments, doctors, patients, and monitor hospital analytics.</p>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="user-role-card">
                    <div class="role-icon">👨‍⚕️</div>
                    <h5 class="role-title">Doctors</h5>
                    <p class="role-text">View appointments, manage availability, and record patient treatments.</p>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="user-role-card">
                    <div class="role-icon">🧑‍🦱</div>
                    <h5 class="role-title">Patients</h5>
                    <p class="role-text">Book appointments, view medical history, and access treatment records.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Our Mission -->
        <div class="col-12">
          <div class="card info-card mission-card">
            <div class="card-body text-center">
              <div class="icon-circle mx-auto mb-3">💡</div>
              <h2 class="section-title">Our Mission</h2>
              <p class="mission-text">
                We believe in making healthcare more accessible, efficient, and patient-centric through innovative 
                technology. Our system bridges the gap between healthcare providers and patients, ensuring seamless 
                communication and better health outcomes for everyone.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.about-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.about-subtitle {
  font-size: 1.2rem;
  color: #6b7280;
  font-weight: 400;
}

.info-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
}

.info-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.icon-circle {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin-right: 1rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #1f2937;
}

.info-text {
  font-size: 1.1rem;
  color: #4b5563;
  line-height: 1.8;
  margin: 0;
}

.feature-item {
  display: flex;
  gap: 1rem;
  align-items: start;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  transition: background 0.2s;
}

.feature-item:hover {
  background: #f3f4f6;
}

.feature-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.feature-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.feature-text {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.user-role-card {
  text-align: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
  height: 100%;
}

.user-role-card:hover {
  border-color: #6366f1;
  transform: scale(1.05);
}

.role-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.role-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.role-text {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
}

.mission-card {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
}

.mission-card .icon-circle {
  background: rgba(255, 255, 255, 0.2);
}

.mission-card .section-title {
  color: white;
  margin-bottom: 1rem;
}

.mission-text {
  font-size: 1.15rem;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.95);
  max-width: 800px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .about-title {
    font-size: 2rem;
  }
  
  .about-subtitle {
    font-size: 1rem;
  }
  
  .section-title {
    font-size: 1.5rem;
  }
  
  .feature-item {
    padding: 0.75rem;
  }
  
  .user-role-card {
    padding: 1.5rem 1rem;
  }
}
</style>
