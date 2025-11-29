<script setup>
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const router = useRouter()
const route = useRoute()

const INACTIVITY_TIMEOUT = 5 * 60 * 1000 // 5 minutes in milliseconds
let inactivityTimer = null

function safeParseUser() {
  try {
    const raw = localStorage.getItem('user')
    if (!raw || raw === 'undefined') return null
    return JSON.parse(raw)
  } catch (e) {
    console.error('Failed to parse user from localStorage:', e)
    return null
  }
}

const user = ref(safeParseUser())
const showLogoutModal = ref(false)

// Watch for route changes and refresh user state
watch(() => route.path, () => {
  user.value = safeParseUser()
})

// Also refresh on mount
onMounted(() => {
  user.value = safeParseUser()
  if (user.value) {
    setupInactivityTimer()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  clearInactivityTimer()
})

// Watch user state to setup/clear timer
watch(user, (newUser) => {
  if (newUser) {
    setupInactivityTimer()
  } else {
    clearInactivityTimer()
  }
})

function logout() {
  showLogoutModal.value = true
}

function confirmLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  clearInactivityTimer()
  showLogoutModal.value = false
  router.push('/')
}

function cancelLogout() {
  showLogoutModal.value = false
}

function autoLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  clearInactivityTimer()
  alert('You have been logged out due to inactivity.')
  router.push('/')
}

function resetInactivityTimer() {
  if (user.value) {
    clearInactivityTimer()
    inactivityTimer = setTimeout(autoLogout, INACTIVITY_TIMEOUT)
  }
}

function clearInactivityTimer() {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer)
    inactivityTimer = null
  }
}

function setupInactivityTimer() {
  // Clear any existing timer
  clearInactivityTimer()
  
  // Set initial timer
  inactivityTimer = setTimeout(autoLogout, INACTIVITY_TIMEOUT)
  
  // Activity events to track
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  
  // Add event listeners to reset timer on user activity
  events.forEach(event => {
    document.addEventListener(event, resetInactivityTimer, true)
  })
}

// Watch for route changes to reset timer
watch(() => route.path, () => {
  resetInactivityTimer()
})

const showSidebar = computed(() => {
  // Show sidebar only for logged-in users on role-specific pages
  return user.value && route.path !== '/in' && route.path !== '/about'
})

const navLinks = computed(() => {
  if (!user.value) return []
  const role = user.value.role
  
  if (role === 'admin') {
    return [
      { label: 'Dashboard', to: '/admin', icon: '📊' },
      { label: 'Departments', to: '/admin/departments', icon: '🏥' },
      { label: 'Doctors', to: '/admin/doctors', icon: '👨‍⚕️' },
      { label: 'Patients', to: '/admin/patients', icon: '👤' },
      { label: 'Appointments', to: '/admin/appointments', icon: '📅' }
    ]
  }
  
  if (role === 'doctor') {
    return [
      { label: 'Dashboard', to: '/doctor', icon: '📊' },
      { label: 'Patient History', to: '/doctor/patients', icon: '📋' }
    ]
  }
  
  if (role === 'patient') {
    return [
      { label: 'Dashboard', to: '/patient', icon: '📊' },
      { label: 'Book Appointment', to: '/patient/book', icon: '➕' },
      { label: 'My Appointments', to: '/patient/appointments', icon: '📅' },
      { label: 'My Profile', to: '/patient/profile', icon: '👤' }
    ]
  }
  
  return []
})
</script>

<template>
  <div id="app">
    <!-- Minimal Notion-like sticky header -->
    <header class="app-header">
      <div class="container-fluid px-4 d-flex justify-content-between align-items-center py-2">
        <div class="d-flex align-items-center" style="margin-left: 1.5rem;">
          <RouterLink to="/" class="hms-logo text-decoration-none">HMS</RouterLink>
        </div>
        <div class="d-flex align-items-center gap-3" style="margin-right: 1.5rem;">
          <template v-if="user">
            <span class="user-name">
              {{ user.name }}
            </span>
            <button class="btn btn-logout" @click="logout">Logout</button>
          </template>
          <template v-else>
            <RouterLink to="/in" class="btn btn-login">Login</RouterLink>
          </template>
        </div>
      </div>
    </header>

    <!-- Secondary Navigation for logged-in users -->
    <nav v-if="user && navLinks.length" class="secondary-nav">
      <div class="container">
        <div class="nav-links-wrapper justify-content-center">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="nav-link-item"
            active-class="active"
          >
            <span class="nav-icon">{{ link.icon }}</span>
            <span class="nav-label">{{ link.label }}</span>
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Main layout with optional sidebar -->
    <main class="app-main">
      <div class="container">
        <RouterView />
      </div>
    </main>

    <!-- Logout Confirmation Modal -->
    <div v-if="showLogoutModal" class="modal-overlay" @click="cancelLogout">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">👋 Confirm Logout</h3>
          <button class="close-btn" @click="cancelLogout">&times;</button>
        </div>
        <div class="modal-body">
          <p class="modal-text">Are you sure you want to logout?</p>
          <p class="modal-subtext">You'll need to login again to access your dashboard and appointments.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="cancelLogout">Cancel</button>
          <button class="btn-logout" @click="confirmLogout">Logout</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-header {
  background: #000000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.hms-logo {
  font-weight: 900;
  font-size: 2rem;
  letter-spacing: 1px;
  color: #ffffff;
  transition: color 0.3s;
}

.hms-logo:hover {
  color: #a5b4fc !important;
}

.nav-link {
  font-size: 1.1rem;
  font-weight: 500;
  text-decoration: none;
  color: #d1d5db;
  transition: color 0.3s;
}

.nav-link:hover {
  color: #ffffff !important;
}

.user-name {
  font-size: 1rem;
  font-weight: 500;
  color: #d1d5db;
}

.btn-login {
  padding: 0.6rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s;
  background: #0d6efd;
  color: white;
  border: none;
  text-decoration: none;
  display: inline-block;
}

.btn-login:hover {
  background: #0b5ed7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

.btn-logout {
  padding: 0.6rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s;
  background: #dc3545;
  color: white;
  border: none;
}

.btn-logout:hover {
  background: #bb2d3b;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

/* Secondary Navigation */
.secondary-nav {
  background: #000000;
  border-bottom: 1px solid #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-links-wrapper {
  display: flex;
  gap: 0;
  overflow-x: auto;
  scrollbar-width: none;
}

.nav-links-wrapper::-webkit-scrollbar {
  display: none;
}

.nav-link-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.25rem;
  color: #d1d5db;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.3s;
  border-bottom: 3px solid transparent;
}

.nav-link-item:hover {
  background: #1a1a1a;
  color: #ffffff;
}

.nav-link-item.active {
  color: #ffffff;
  background: #1a1a1a;
  border-bottom-color: #6366f1;
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-label {
  font-size: 0.95rem;
}

.layout-with-sidebar {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
  margin-top: 16px;
}

.sidebar-col {
  position: sticky;
  top: 72px;
  align-self: start;
}

.content-col {
  min-width: 0;
}

@media (max-width: 768px) {
  .nav-link-item {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
  
  .nav-icon {
    font-size: 1rem;
  }
  
  .nav-label {
    font-size: 0.85rem;
  }
  
  .layout-with-sidebar {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .sidebar-col {
    position: static;
  }
}

/* Logout Modal */
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

.btn-cancel, .btn-logout {
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

.btn-logout {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn-logout:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-cancel, .btn-logout {
    width: 100%;
  }
}
</style>
