<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()

function safeParseUser() {
  try {
    const raw = localStorage.getItem('user')
    if (!raw || raw === 'undefined') return null
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

const user = computed(() => safeParseUser())

const adminLinks = [
  { label: 'Dashboard', to: '/admin', icon: '📊' },
  { label: 'Departments', to: '/admin/departments', icon: '🏥' },
  { label: 'Doctors', to: '/admin/doctors', icon: '👨‍⚕️' },
  { label: 'Patients', to: '/admin/patients', icon: '👤' },
  { label: 'Appointments', to: '/admin/appointments', icon: '📅' }
]

const doctorLinks = [
  { label: 'Dashboard', to: '/doctor', icon: '📊' },
  { label: 'Patient History', to: '/doctor/patients', icon: '📋' }
]

const patientLinks = [
  { label: 'Dashboard', to: '/patient', icon: '📊' },
  { label: 'Book Appointment', to: '/patient/book', icon: '➕' },
  { label: 'My Appointments', to: '/patient/appointments', icon: '📅' },
  { label: 'My Profile', to: '/patient/profile', icon: '👤' }
]

const navLinks = computed(() => {
  if (!user.value) return []
  if (user.value.role === 'admin') return adminLinks
  if (user.value.role === 'doctor') return doctorLinks
  if (user.value.role === 'patient') return patientLinks
  return []
})
</script>

<template>
  <nav v-if="navLinks.length" :class="['nav-sidebar', (user && user.role) ? `role-${user.role}` : '']">
    <RouterLink
      v-for="link in navLinks"
      :key="link.to"
      :to="link.to"
      class="nav-item"
      active-class="active"
    >
      <span class="nav-icon">{{ link.icon }}</span>
      <span class="nav-label">{{ link.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.nav-sidebar {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fafc 0%, #f3f4f6 100%);
  border: 1px solid var(--border);
}

/* Role accent palettes */
.role-admin {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #c7d2fe;
}
.role-doctor {
  background: linear-gradient(180deg, #ecfeff 0%, #cffafe 100%);
  border-color: #a5f3fc;
}
.role-patient {
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #bbf7d0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  color: var(--muted);
  text-decoration: none;
  transition: all 0.15s;
  font-weight: 600;
}

.nav-item:hover {
  background: rgba(0,0,0,0.035);
  color: var(--text);
}

.nav-item.active {
  background: #e0e7ff;
  color: var(--primary);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 14px;
}

@media (max-width: 768px) {
  .nav-sidebar {
    flex-direction: row;
    overflow-x: auto;
    padding: 8px 0;
  }
  .nav-item {
    flex-direction: column;
    padding: 8px 12px;
    gap: 4px;
    white-space: nowrap;
  }
  .nav-label {
    font-size: 11px;
  }
}
</style>
