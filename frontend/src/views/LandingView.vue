<template>
  <div class="landing-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <h1 class="hero-title">Your Health, Our Priority.</h1>
        <div class="search-bar-wrapper">
          <input 
            type="text" 
            class="search-input" 
            placeholder="Search Doctors by Name, Specialty, or Location..."
            v-model="searchQuery"
            @keyup.enter="handleSearch"
          >
          <button class="search-btn" @click="handleSearch">
            <span class="search-icon">🔍</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Services Section -->
    <section class="services-section">
      <div class="container">
        <div class="row g-4">
          <div class="col-12 col-md-4">
            <div class="service-card" @click="goToBooking">
              <div class="service-icon">📅</div>
              <h3 class="service-title">Book Appointments</h3>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="service-card" @click="goToLogin">
              <div class="service-icon">📋</div>
              <h3 class="service-title">Access Medical Records</h3>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="service-card" @click="goToLogin">
              <div class="service-icon">👨‍⚕️</div>
              <h3 class="service-title">Best Doctors</h3>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- About Section -->
    <section class="about-section">
      <div class="container">
        <div class="text-center mb-5">
          <h2 class="about-section-title">About Our Hospital Management System</h2>
          <p class="about-section-subtitle">Transforming Healthcare Through Technology</p>
        </div>

        <div class="row g-4">
          <!-- What We Do -->
          <div class="col-12">
            <div class="card info-card">
              <div class="card-body">
                <div class="d-flex align-items-center mb-3">
                  <div class="icon-circle-small">🏥</div>
                  <h3 class="info-section-title mb-0">What We Do</h3>
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
                  <div class="icon-circle-small">✨</div>
                  <h3 class="info-section-title mb-0">Key Features</h3>
                </div>
                <div class="row g-3">
                  <div class="col-md-6">
                    <div class="feature-item">
                      <div class="feature-icon-small">📅</div>
                      <div>
                        <h5 class="feature-title-small">Easy Appointment Booking</h5>
                        <p class="feature-text-small">Schedule appointments with doctors across multiple departments.</p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="feature-item">
                      <div class="feature-icon-small">👨‍⚕️</div>
                      <div>
                        <h5 class="feature-title-small">Find Specialized Doctors</h5>
                        <p class="feature-text-small">Search and connect with expert doctors by specialization.</p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="feature-item">
                      <div class="feature-icon-small">📋</div>
                      <div>
                        <h5 class="feature-title-small">Medical Records Management</h5>
                        <p class="feature-text-small">Access your complete treatment history and prescriptions anytime.</p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="feature-item">
                      <div class="feature-icon-small">🔔</div>
                      <div>
                        <h5 class="feature-title-small">Automated Reminders</h5>
                        <p class="feature-text-small">Receive email notifications for upcoming appointments.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="container">
        <div class="text-center text-muted small">
          © 2025 Hospital Management System
        </div>
      </div>
    </footer>

    <!-- Login Required Modal -->
    <div v-if="showLoginModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">🔒 Login Required</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <p class="modal-text">Please login to use our services and search for doctors.</p>
          <p class="modal-subtext">Access personalized healthcare services, book appointments, and manage your medical records.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">Cancel</button>
          <button class="btn-login" @click="goToLogin">Login Now</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchQuery = ref('')
const showLoginModal = ref(false)

function goToLogin() {
  showLoginModal.value = false
  router.push('/in')
}

function closeModal() {
  showLoginModal.value = false
}

function goToBooking() {
  const token = localStorage.getItem('token')
  if (!token) {
    showLoginModal.value = true
    return
  }
  // If logged in, route by role
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    const role = user?.role
    if (role === 'admin') return router.push('/admin')
    if (role === 'doctor') return router.push('/doctor')
    return router.push('/patient/book')
  } catch {
    showLoginModal.value = true
  }
}

function handleSearch() {
  const token = localStorage.getItem('token')
  if (!token) {
    showLoginModal.value = true
    return
  }
  goToBooking()
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
}

/* Hero part */
.hero-section {
  position: relative;
  height: 70vh;
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  margin-right: calc(-50vw + 50%);
  background: linear-gradient(180deg, #1a103a 0%, #5038aeff 40%, #b4a5d9 70%, rgba(244, 244, 249, 0.95) 90%, #ffffff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 900px;
  padding: 0 20px;
}

.hero-title {
  color: #ffffff;
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.search-bar-wrapper {
  position: relative;
  max-width: 700px;
  margin: 0 auto;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border-radius: 50px;
  overflow: hidden;
}

.search-input {
  width: 100%;
  padding: 18px 70px 18px 30px;
  border: none;
  font-size: 1rem;
  outline: none;
  border-radius: 50px;
}

.search-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: #6366f1;
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.3s;
}

.search-btn:hover {
  background: #4f46e5;
}

.search-icon {
  font-size: 1.5rem;
}

/* Services Section */
.services-section {
  padding: 80px 20px;
  background: #f8f9fa;
}

.service-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 40px 30px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  height: 100%;
}

.service-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.service-icon {
  font-size: 3.5rem;
  margin-bottom: 20px;
  background: #6366f1;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: #ffffff;
}

.service-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

/* About Section */
.about-section {
  padding: 80px 20px;
  background: #ffffff;
}

.about-section-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.about-section-subtitle {
  font-size: 1.1rem;
  color: #6b7280;
}

.info-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
}

.info-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.icon-circle-small {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-right: 1rem;
}

.info-section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
}

.info-text {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.7;
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

.feature-icon-small {
  font-size: 1.75rem;
  flex-shrink: 0;
}

.feature-title-small {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.feature-text-small {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

/* Footer */
.landing-footer {
  background: #1a1a2e;
  padding: 20px;
  color: #a0a0a0;
  text-align: center;
}

/* Login Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 24px;
}

.modal-text {
  font-size: 1.1rem;
  color: #374151;
  margin: 0 0 12px 0;
  font-weight: 500;
}

.modal-subtext {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
}

.modal-footer {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel, .btn-login {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-login {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-login:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .search-input {
    font-size: 0.9rem;
    padding: 15px 60px 15px 20px;
  }
  
  .search-btn {
    width: 45px;
    height: 45px;
  }
  
  .services-section {
    padding: 50px 20px;
  }

  .modal-content {
    width: 95%;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-cancel, .btn-login {
    width: 100%;
  }
}
</style>
