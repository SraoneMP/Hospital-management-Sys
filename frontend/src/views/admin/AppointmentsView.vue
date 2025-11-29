<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

const route = useRoute()
const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const appointments = ref([])

const filters = ref({
  q: '',
  status: '',
  from: '',
  to: ''
})

const fetchAppointments = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/appointments', { headers: authHeader })
    appointments.value = data.appointments || []
    
    // Apply status filter from query parameter if present
    const statusFromQuery = route.query.status
    if (statusFromQuery) {
      // Map dashboard status to appointment status
      if (statusFromQuery === 'upcoming') {
        filters.value.status = 'Booked'
      } else if (statusFromQuery === 'completed') {
        filters.value.status = 'Completed'
      } else if (statusFromQuery === 'cancelled') {
        filters.value.status = 'Cancelled'
      }
    }
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load appointments'
  } finally {
    loading.value = false
  }
}

const matchesFilters = (a) => {
  // status
  if (filters.value.status && a.status !== filters.value.status) return false
  // date range
  if (filters.value.from && a.appointment_date < filters.value.from) return false
  if (filters.value.to && a.appointment_date > filters.value.to) return false
  // search q across doctor/patient names
  const q = (filters.value.q || '').toLowerCase()
  if (q) {
    const doc = (a.doctor_name || '').toLowerCase()
    const pat = (a.patient_name || '').toLowerCase()
    if (!doc.includes(q) && !pat.includes(q)) return false
  }
  return true
}

const upcoming = computed(() =>
  (appointments.value || [])
    .filter(a => a.status === 'Booked')
    .filter(matchesFilters)
    .sort((a, b) => (a.appointment_date + a.appointment_time).localeCompare(b.appointment_date + b.appointment_time))
)

const past = computed(() =>
  (appointments.value || [])
    .filter(a => a.status !== 'Booked')
    .filter(matchesFilters)
    .sort((a, b) => (b.appointment_date + b.appointment_time).localeCompare(a.appointment_date + a.appointment_time))
)

const applyFilters = () => {
  // computed lists react automatically; function kept for form submit UX
}

const resetFilters = () => {
  filters.value = { q: '', status: '', from: '', to: '' }
}

// Cancel appointment (admin)
const canceling = ref(false)
const cancelAppointment = async (appt) => {
  if (!confirm('Cancel this appointment?')) return
  try {
    canceling.value = true
    await axios.delete(`/api/appointments/${appt.id}`, { headers: authHeader })
    await fetchAppointments()
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.message || 'Failed to cancel appointment')
  } finally {
    canceling.value = false
  }
}

onMounted(fetchAppointments)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Manage Appointments</h2>
      <div class="text-muted small">Total: {{ appointments.length }}</div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <form class="row g-2 align-items-end" @submit.prevent="applyFilters">
          <div class="col-12 col-md-4">
            <label class="form-label">Search (Doctor / Patient)</label>
            <input v-model="filters.q" class="form-control" placeholder="Type a name" />
          </div>
          <div class="col-6 col-md-2">
            <label class="form-label">Status</label>
            <select v-model="filters.status" class="form-select">
              <option value="">All</option>
              <option value="Booked">Booked</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div class="col-6 col-md-2">
            <label class="form-label">From</label>
            <input v-model="filters.from" type="date" class="form-control" />
          </div>
          <div class="col-6 col-md-2">
            <label class="form-label">To</label>
            <input v-model="filters.to" type="date" class="form-control" />
          </div>
          <div class="col-6 col-md-2 d-grid">
            <button class="btn btn-primary" type="submit">Apply</button>
          </div>
          <div class="col-12 col-md-2 d-grid mt-2 mt-md-0">
            <button class="btn btn-outline-secondary" type="button" @click="resetFilters">Reset</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="loading" class="alert alert-info">Loading...</div>
    <div v-else>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <!-- Upcoming -->
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5 class="mb-0">Upcoming (Booked)</h5>
          </div>
          <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Doctor</th>
                  <th>Patient</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in upcoming" :key="a.id">
                  <td>{{ a.appointment_date }}</td>
                  <td>{{ a.appointment_time }}</td>
                  <td>{{ a.doctor_name }}</td>
                  <td>{{ a.patient_name }}</td>
                  <td><span class="badge bg-info">{{ a.status }}</span></td>
                  <td>{{ a.reason }}</td>
                  <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" :disabled="canceling" @click="cancelAppointment(a)">Cancel</button>
                  </td>
                </tr>
                <tr v-if="!upcoming.length">
                  <td colspan="7" class="text-muted">No matching upcoming appointments.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Past -->
      <div class="card">
        <div class="card-body">
          <h5 class="mb-2">Past (Completed / Cancelled)</h5>
          <div class="table-responsive">
            <table class="table table-sm table-bordered align-middle">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Doctor</th>
                  <th>Patient</th>
                  <th>Status</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in past" :key="a.id">
                  <td>{{ a.appointment_date }}</td>
                  <td>{{ a.appointment_time }}</td>
                  <td>{{ a.doctor_name }}</td>
                  <td>{{ a.patient_name }}</td>
                  <td>
                    <span :class="['badge', a.status === 'Completed' ? 'bg-success' : 'bg-secondary']">{{ a.status }}</span>
                  </td>
                  <td>{{ a.reason }}</td>
                </tr>
                <tr v-if="!past.length">
                  <td colspan="6" class="text-muted">No matching past appointments.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<style scoped>
.container { max-width: 1100px; }
</style>
