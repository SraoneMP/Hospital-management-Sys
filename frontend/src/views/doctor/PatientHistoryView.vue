<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const appointments = ref([])
const selectedAppt = ref(null)

// Treatment modal
const treatmentModal = ref(false)
const treatmentForm = ref({
  diagnosis: '',
  prescription: '',
  notes: '',
  next_visit: ''
})
const treatmentError = ref('')
const treatmentSuccess = ref('')

const fetchAppointments = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/appointments', { headers: authHeader })
    appointments.value = (data.appointments || []).filter(a => a.status === 'Completed')
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load appointments'
  } finally {
    loading.value = false
  }
}

const groupedByPatient = computed(() => {
  const map = {}
  appointments.value.forEach(a => {
    const pid = a.patient_id
    const pname = a.patient_name || 'Unknown'
    if (!map[pid]) {
      map[pid] = { id: pid, name: pname, appointments: [] }
    }
    map[pid].appointments.push(a)
  })
  return Object.values(map).sort((a, b) => a.name.localeCompare(b.name))
})

const openTreatment = (appt) => {
  selectedAppt.value = appt
  // If treatment exists, prefill
  if (appt.treatment) {
    treatmentForm.value = {
      diagnosis: appt.treatment.diagnosis || '',
      prescription: appt.treatment.prescription || '',
      notes: appt.treatment.notes || '',
      next_visit: appt.treatment.next_visit || ''
    }
  } else {
    treatmentForm.value = { diagnosis: '', prescription: '', notes: '', next_visit: '' }
  }
  treatmentError.value = ''
  treatmentSuccess.value = ''
  treatmentModal.value = true
}

const closeTreatment = () => {
  treatmentModal.value = false
  selectedAppt.value = null
  treatmentForm.value = { diagnosis: '', prescription: '', notes: '', next_visit: '' }
  treatmentError.value = ''
  treatmentSuccess.value = ''
}

const saveTreatment = async () => {
  treatmentError.value = ''
  treatmentSuccess.value = ''
  if (!treatmentForm.value.diagnosis) {
    treatmentError.value = 'Diagnosis is required'
    return
  }
  try {
    const payload = {
      diagnosis: treatmentForm.value.diagnosis,
      prescription: treatmentForm.value.prescription,
      notes: treatmentForm.value.notes,
      next_visit: treatmentForm.value.next_visit || null
    }
    // If treatment already exists, use PUT else POST
    const method = selectedAppt.value.treatment ? 'put' : 'post'
    await axios[method](`/api/appointments/${selectedAppt.value.id}/treatment`, payload, { headers: authHeader })
    treatmentSuccess.value = 'Treatment saved successfully'
    setTimeout(async () => {
      closeTreatment()
      await fetchAppointments()
    }, 800)
  } catch (e) {
    console.error(e)
    treatmentError.value = e.response?.data?.message || 'Failed to save treatment'
  }
}

onMounted(fetchAppointments)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Patient History & Treatments</h2>
      <button class="btn btn-sm btn-outline-secondary" @click="router.push('/doctor')">Back to Dashboard</button>
    </div>

    <div v-if="loading" class="alert alert-info">Loading...</div>
    <div v-else>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-if="!groupedByPatient.length" class="alert alert-warning">
        No completed appointments with treatments yet.
      </div>

      <div v-for="pg in groupedByPatient" :key="pg.id" class="card mb-3">
        <div class="card-body">
          <h5 class="mb-2">{{ pg.name }}</h5>
          <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Diagnosis</th>
                  <th>Prescription</th>
                  <th>Next Visit</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in pg.appointments" :key="a.id">
                  <td>{{ a.appointment_date }}</td>
                  <td>{{ a.appointment_time }}</td>
                  <td>{{ a.treatment?.diagnosis || '-' }}</td>
                  <td>{{ a.treatment?.prescription || '-' }}</td>
                  <td>{{ a.treatment?.next_visit || '-' }}</td>
                  <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary" @click="openTreatment(a)">
                      {{ a.treatment ? 'Update' : 'Add' }} Treatment
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Treatment Modal -->
    <div v-if="treatmentModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Treatment Details</h5>
            <button type="button" class="btn-close" @click="closeTreatment"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveTreatment" class="row g-2">
              <div class="col-12">
                <label class="form-label">Diagnosis *</label>
                <textarea v-model="treatmentForm.diagnosis" class="form-control" rows="3" required></textarea>
              </div>
              <div class="col-12">
                <label class="form-label">Prescription</label>
                <textarea v-model="treatmentForm.prescription" class="form-control" rows="2"></textarea>
              </div>
              <div class="col-12">
                <label class="form-label">Notes</label>
                <textarea v-model="treatmentForm.notes" class="form-control" rows="2"></textarea>
              </div>
              <div class="col-md-6">
                <label class="form-label">Next Visit Date</label>
                <input v-model="treatmentForm.next_visit" type="date" class="form-control" />
              </div>

              <div v-if="treatmentError" class="alert alert-danger">{{ treatmentError }}</div>
              <div v-if="treatmentSuccess" class="alert alert-success">{{ treatmentSuccess }}</div>

              <div class="d-flex gap-2">
                <button class="btn btn-primary" type="submit">Save</button>
                <button class="btn btn-secondary" type="button" @click="closeTreatment">Close</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.container { max-width: 1100px; }
.modal { display: block; }
</style>
