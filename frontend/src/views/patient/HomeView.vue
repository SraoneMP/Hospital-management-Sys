<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const departments = ref([])
const availability = ref([])
const upcoming = ref([])
const history = ref([])
const router = useRouter()
const exporting = ref(false)
const exportMessage = ref('')

const emojiFor = (name) => {
  const n = (name || '').toLowerCase()
  if (n.includes('cardio')) return '❤️'
  if (n.includes('derma')) return '🧴'
  if (n.includes('neuro')) return '🧠'
  if (n.includes('ortho') || n.includes('bone')) return '🦴'
  if (n.includes('pedia') || n.includes('child')) return '🍼'
  if (n.includes('general')) return '🩺'
  return '🏥'
}
const gotoDept = (dept) => {
  const deptName = dept?.name || ''
  router.push({ path: '/patient/book', query: { department: deptName } })
}

const fetchDashboard = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/patient/dashboard', {
      headers: authHeader
    })
    departments.value = data.departments || []
    availability.value = data.availability_next_week || []
    upcoming.value = data.upcoming_appointments || []
    history.value = data.history || []
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load patient dashboard'
  } finally {
    loading.value = false
  }
}

const exportCSV = async () => {
  exporting.value = true
  exportMessage.value = ''
  try {
    const { data } = await axios.post('/api/patient/export/async', {}, {
      headers: authHeader
    })
    exportMessage.value = data.message || 'Export started! You will receive an email with the CSV file shortly.'
    setTimeout(() => {
      exportMessage.value = ''
    }, 5000)
  } catch (e) {
    console.error(e)
    exportMessage.value = e.response?.data?.message || 'Failed to start export'
    setTimeout(() => {
      exportMessage.value = ''
    }, 5000)
  } finally {
    exporting.value = false
  }
}


onMounted(fetchDashboard)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Patient Dashboard</h2>
      <div class="d-flex gap-2">
        <router-link to="/patient/book" class="btn btn-sm btn-primary">Book Appointment</router-link>
        <button 
          @click="exportCSV" 
          :disabled="exporting"
          class="btn btn-sm btn-success"
        >
          <span v-if="exporting">Exporting...</span>
          <span v-else>Export CSV</span>
        </button>
      </div>
    </div>

    <div v-if="exportMessage" class="alert" :class="exportMessage.includes('Failed') ? 'alert-danger' : 'alert-success'" role="alert">
      {{ exportMessage }}
    </div>

    <div v-if="loading" class="alert alert-info mb-3">Loading...</div>
    <div v-else-if="error" class="alert alert-danger mb-3">{{ error }}</div>

    <div v-else>
      <div class="row g-3">
        <!-- Departments -->
        <div class="col-12">
          <div class="card h-100 mb-2">
            <div class="card-body">
              <h5 class="mb-3">Departments & Specializations</h5>
              <div class="row g-3">
                <div v-for="dept in departments" :key="dept.id" class="col-12 col-md-6 col-lg-4">
                  <div class="card h-100" role="button" style="cursor:pointer" @click="gotoDept(dept)">
                    <div class="card-body">
                      <div class="d-flex justify-content-between align-items-start">
                        <h6 class="card-title mb-1">{{ emojiFor(dept.name) }} {{ dept.name }}</h6>
                      </div>
                      <p class="card-text small text-muted mb-2">{{ dept.description }}</p>
                      <div class="d-flex justify-content-end">
                        <span class="badge rounded-pill bg-secondary">{{ dept.doctors_registered }} doctors</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="!departments.length" class="text-muted small">
                  No departments found.
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Availability next week -->
        <div class="col-12">
          <div class="card mb-2">
            <div class="card-body">
              <h5 class="mb-2">Doctors Availability (Next 7 days)</h5>
              <div class="table-responsive">
                <table class="table table-sm table-striped">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Start</th>
                      <th>End</th>
                      <th>Doctor ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="slot in availability" :key="slot.id">
                      <td>{{ slot.available_date }}</td>
                      <td>{{ slot.start_time }}</td>
                      <td>{{ slot.end_time }}</td>
                      <td>{{ slot.doctor_id }}</td>
                    </tr>
                    <tr v-if="!availability.length">
                      <td colspan="4" class="text-muted">No availability found.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Upcoming appointments -->
        <div class="col-12">
          <div class="card mb-2">
            <div class="card-body">
              <h5 class="mb-2">Upcoming Appointments</h5>
              <div class="table-responsive">
                <table class="table table-sm table-hover">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Doctor</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in upcoming" :key="a.id">
                      <td>{{ a.appointment_date }}</td>
                      <td>{{ a.appointment_time }}</td>
                      <td>{{ a.doctor_name }}</td>
                      <td><span class="badge bg-info">{{ a.status }}</span></td>
                    </tr>
                    <tr v-if="!upcoming.length">
                      <td colspan="4" class="text-muted">No upcoming appointments.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Past appointments & treatments tht is done -->
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <h5 class="mb-2">Past Appointments & Treatments</h5>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Doctor</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="h in history" :key="h.id">
                      <td>{{ h.appointment_date }}</td>
                      <td>{{ h.appointment_time }}</td>
                      <td>{{ h.doctor_name }}</td>
                      <td>
                        <span :class="['badge', h.status === 'Completed' ? 'bg-success' : 'bg-secondary']">{{ h.status }}</span>
                      </td>
                    </tr>
                    <tr v-if="!history.length">
                      <td colspan="4" class="text-muted">No past appointments.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

      </div> <!-- /row -->
    </div>
  </div>
</template>

<style scoped>
.container { max-width: 1100px; }
</style>
