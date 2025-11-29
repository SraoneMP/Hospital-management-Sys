<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// keep auth header handy
const rawToken = localStorage.getItem('token') || ''
const auth = { Authorization: `Bearer ${rawToken}` }

// main list
const isBusy = ref(true)
const oops = ref('')
const appts = ref([])

// fetch my appointments (role-based on backend)
async function loadMine() {
  isBusy.value = true
  oops.value = ''
  try {
    const { data } = await axios.get('/api/appointments', { headers: auth })
    appts.value = data.appointments || []
  } catch (err) {
    console.error(err)
    oops.value = err?.response?.data?.message || 'Failed to load appointments'
  } finally {
    isBusy.value = false
  }
}

// just sort them in a way that reads well
const upcomingRows = computed(() =>
  (appts.value || [])
    .filter(a => a.status === 'Booked')
    .sort((a, b) => (a.appointment_date + a.appointment_time).localeCompare(b.appointment_date + b.appointment_time))
)
const pastRows = computed(() =>
  (appts.value || [])
    .filter(a => a.status !== 'Booked')
    .sort((a, b) => (b.appointment_date + b.appointment_time).localeCompare(a.appointment_date + a.appointment_time))
)

// cancel flow (simple, with confirm)
const isCancelling = ref(false)
async function cancelOne(appt) {
  if (!confirm('Are you sure you want to cancel this appointment?')) return
  try {
    isCancelling.value = true
    await axios.delete(`/api/appointments/${appt.id}`, { headers: auth })
    await loadMine()
  } catch (err) {
    console.error(err)
    alert(err?.response?.data?.message || 'Failed to cancel appointment')
  } finally {
    isCancelling.value = false
  }
}

// reschedule drawer
const showRes = ref(false)
const picked = ref(null)
const resDraft = ref({ date: '', time: '' })
const resOops = ref('')
const resOk = ref('')
function openRes(appt) {
  picked.value = appt
  resDraft.value = { date: appt.appointment_date, time: appt.appointment_time }
  resOops.value = ''
  resOk.value = ''
  showRes.value = true
}
function closeRes() {
  showRes.value = false
  picked.value = null
  resDraft.value = { date: '', time: '' }
  resOops.value = ''
  resOk.value = ''
}
async function sendRes() {
  resOops.value = ''
  resOk.value = ''
  if (!resDraft.value.date || !resDraft.value.time) {
    resOops.value = 'Date and time are required'
    return
  }
  try {
    await axios.patch(`/api/appointments/${picked.value.id}`, {
      date: resDraft.value.date,
      time: resDraft.value.time
    }, { headers: auth })
    resOk.value = 'Rescheduled'
    setTimeout(async () => {
      closeRes()
      await loadMine()
    }, 700)
  } catch (err) {
    console.error(err)
    resOops.value = err?.response?.data?.message || 'Failed to reschedule'
  }
}

/* read-only treatment peek */
const showTreat = ref(false)
const treatBusy = ref(false)
const treatErr = ref('')
const treatData = ref(null)
const isExportingId = ref(null)

async function openTreat(appt) {
  showTreat.value = true
  treatBusy.value = true
  treatErr.value = ''
  treatData.value = null
  try {
    const { data } = await axios.get(`/api/appointments/${appt.id}/treatment`, { headers: auth })
    treatData.value = data.treatment || null
  } catch (err) {
    treatErr.value = err?.response?.data?.message || 'Failed to load treatment'
  } finally {
    treatBusy.value = false
  }
}
function closeTreat() {
  showTreat.value = false
  treatData.value = null
}

function csvEscape(val) {
  if (val == null) return '""'
  const s = String(val).replace(/"/g, '""')
  return `"${s}"`
}

async function exportOneCSV(appt) {
  try {
    isExportingId.value = appt.id
    // fetch treatment for this exact visit
    const { data } = await axios.get(`/api/appointments/${appt.id}/treatment`, { headers: auth })
    const t = data?.treatment
    if (!t) {
      alert('No treatment found for this appointment')
      return
    }

    // gather minimal patient context from local storage (name/email)
    let user = null
    try { user = JSON.parse(localStorage.getItem('user') || 'null') } catch {}
    const patientName = user?.name || ''
    const patientEmail = user?.email || ''

    // craft a single-row CSV for this appointment only
    const headers = [
      'Appointment ID',
      'Patient Name',
      'Patient Email',
      'Doctor Name',
      'Appointment Date',
      'Appointment Time',
      'Diagnosis',
      'Prescription',
      'Notes',
      'Next Visit'
    ].join(',')

    const row = [
      csvEscape(appt.id),
      csvEscape(patientName),
      csvEscape(patientEmail),
      csvEscape(appt.doctor_name || ''),
      csvEscape(appt.appointment_date || ''),
      csvEscape(appt.appointment_time || ''),
      csvEscape(t.diagnosis || ''),
      csvEscape(t.prescription || ''),
      csvEscape(t.notes || ''),
      csvEscape(t.next_visit || '')
    ].join(',')

    const csv = '\ufeff' + headers + '\n' + row + '\n'
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `consultation_${appt.id}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error(err)
    alert('Export failed')
  } finally {
    isExportingId.value = null
  }
}

onMounted(loadMine)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">My Appointments</h2>
      <router-link to="/patient/book" class="btn btn-sm btn-primary">Book New Appointment</router-link>
    </div>

    <div v-if="isBusy" class="alert alert-info">Loading...</div>
    <div v-else>
      <div v-if="oops" class="alert alert-danger">{{ oops }}</div>

      <!-- upcoming -->
      <div class="card mb-3">
        <div class="card-body">
          <h5 class="mb-2">Upcoming</h5>
          <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Doctor</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in upcomingRows" :key="a.id">
                  <td>{{ a.appointment_date }}</td>
                  <td>{{ a.appointment_time }}</td>
                  <td>{{ a.doctor_name }}</td>
                  <td><span class="badge bg-info">{{ a.status }}</span></td>
                  <td>{{ a.reason }}</td>
                  <td class="text-end">
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="openRes(a)">Reschedule</button>
                      <button class="btn btn-outline-danger" :disabled="isCancelling" @click="cancelOne(a)">Cancel</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!upcomingRows.length">
                  <td colspan="6" class="text-muted">No upcoming appointments.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- history -->
      <div class="card">
        <div class="card-body">
          <h5 class="mb-2">History</h5>
          <div class="table-responsive">
            <table class="table table-sm table-bordered align-middle">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Doctor</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th>Treatment</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in pastRows" :key="h.id">
                  <td>{{ h.appointment_date }}</td>
                  <td>{{ h.appointment_time }}</td>
                  <td>{{ h.doctor_name }}</td>
                  <td>
                    <span :class="['badge', h.status === 'Completed' ? 'bg-success' : 'bg-secondary']">{{ h.status }}</span>
                  </td>
                  <td>{{ h.reason }}</td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button v-if="h.status === 'Completed'" class="btn btn-outline-primary" @click="openTreat(h)">View</button>
                      <button v-if="h.status === 'Completed'" class="btn btn-outline-secondary" :disabled="isExportingId === h.id" @click="exportOneCSV(h)">
                        {{ isExportingId === h.id ? 'Downloading...' : 'Download' }}
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!pastRows.length">
                  <td colspan="6" class="text-muted">No past appointments.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Treatment details -->
      <div v-if="showTreat" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Treatment Details</h5>
              <button type="button" class="btn-close" @click="closeTreat"></button>
            </div>
            <div class="modal-body">
              <div v-if="treatBusy" class="alert alert-info">Loading...</div>
              <div v-else-if="treatErr" class="alert alert-danger">{{ treatErr }}</div>
              <div v-else-if="treatData">
                <div class="mb-2"><strong>Diagnosis:</strong><br />{{ treatData.diagnosis }}</div>
                <div class="mb-2"><strong>Prescription:</strong><br />{{ treatData.prescription || '-' }}</div>
                <div class="mb-2"><strong>Notes:</strong><br />{{ treatData.notes || '-' }}</div>
                <div class="mb-2"><strong>Next Visit:</strong> {{ treatData.next_visit || '-' }}</div>
              </div>
              <div v-else class="text-muted">No treatment found for this appointment.</div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeTreat">Close</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Reschedule -->
      <div v-if="showRes" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Reschedule Appointment</h5>
              <button type="button" class="btn-close" @click="closeRes"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="sendRes">
                <div class="mb-2">
                  <label class="form-label">New Date</label>
                  <input v-model="resDraft.date" type="date" class="form-control" required>
                </div>
                <div class="mb-2">
                  <label class="form-label">New Time</label>
                  <input v-model="resDraft.time" type="time" class="form-control" required>
                </div>
                <div v-if="resOops" class="alert alert-danger">{{ resOops }}</div>
                <div v-if="resOk" class="alert alert-success">{{ resOk }}</div>
                <div class="d-flex gap-2">
                  <button class="btn btn-primary" type="submit">Save</button>
                  <button class="btn btn-secondary" type="button" @click="closeRes">Close</button>
                </div>
              </form>
              <div class="form-text mt-2">
                Tip: Pick a time within the doctor’s available window.
              </div>
            </div>
          </div>
        </div>
      </div>

    </div> <!-- /loading else -->
  </div>
</template>

<style scoped>
.container { max-width: 1100px; }
.modal { display: block; }
</style>
