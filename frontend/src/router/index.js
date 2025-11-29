import { createRouter, createWebHistory } from 'vue-router'
import PatientHome from '../views/patient/HomeView.vue'

/* read whatever we stashed for the current user; tolerate bad data */
function readUserFromStorage() {
  try {
    const payload = localStorage.getItem('user')
    if (!payload || payload === 'undefined') return null
    return JSON.parse(payload)
  } catch (err) {
    console.warn('Could not parse user from storage:', err)
    return null
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/in',
      name: 'auth',
      component: () => import('../views/AuthView.vue'),
    },
    {
      path: '/admin',
      name: 'adminhome',
      component: () => import('../views/admin/HomeView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/doctor',
      name: 'doctorhome',
      component: () => import('../views/doctor/HomeView.vue'),
      meta: { roles: ['doctor'] },
    },
    {
      path: '/patient',
      name: 'patienthome',
      component: PatientHome,
      meta: { roles: ['patient'] },
    },
    {
      path: '/patient/book',
      name: 'patientbook',
      component: () => import('../views/patient/BookAppointmentView.vue'),
    },
    {
      path: '/patient/profile',
      name: 'patientprofile',
      component: () => import('../views/patient/ProfileView.vue'),
      meta: { roles: ['patient'] },
    },
    {
      path: '/patient/appointments',
      name: 'patientappointments',
      component: () => import('../views/patient/AppointmentsView.vue'),
      meta: { roles: ['patient'] },
    },
    {
      path: '/admin/doctors',
      name: 'admindoctors',
      component: () => import('../views/admin/DoctorsView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/admin/patients',
      name: 'adminpatients',
      component: () => import('../views/admin/PatientsView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/admin/appointments',
      name: 'adminappointments',
      component: () => import('../views/admin/AppointmentsView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/admin/departments',
      name: 'admindepartments',
      component: () => import('../views/admin/DepartmentsView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/doctor/patients',
      name: 'doctorpatients',
      component: () => import('../views/doctor/PatientHistoryView.vue'),
      meta: { roles: ['doctor'] },
    },
    {
      path: '/',
      name: 'landing',
      component: () => import('../views/LandingView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    }
  ]
})

// gentle gatekeeping: keep folks in the right lane
router.beforeEach((to, from, next) => {
  const tokenStr = localStorage.getItem('token')
  const hasAuth = !!tokenStr
  const user = readUserFromStorage()
  const role = user?.role

  // allow public pages without auth
  const publicPages = ['landing', 'auth', 'about']
  if (!hasAuth && !publicPages.includes(to.name)) {
    // Let the landing page handle prompting (modal on Search)
    return next({ name: 'landing' })
  }

  // if logged in and on public page, route to dashboard
  if (hasAuth && publicPages.includes(to.name)) {
    if (role === 'admin') return next({ name: 'adminhome' })
    if (role === 'doctor') return next({ name: 'doctorhome' })
    if (role === 'patient') return next({ name: 'patienthome' })
    return next()
  }

  // role fences
  const required = to.meta?.roles
  if (required && required.length) {
    if (!role || !required.includes(role)) {
      alert('That page is not for your role.')
      if (role === 'admin') return next({ name: 'adminhome' })
      if (role === 'doctor') return next({ name: 'doctorhome' })
      if (role === 'patient') return next({ name: 'patienthome' })
      return next({ name: 'landing' })
    }
  }

  next()
})

export default router;
