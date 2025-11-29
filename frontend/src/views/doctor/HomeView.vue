<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// carry auth like a backpack; nothing fancy
const rawToken = localStorage.getItem('token') || ''
const auth = { Authorization: `Bearer ${rawToken}` }

// dashboard bits
const isBusy = ref(true)
const problem = ref('')
const todaysAppts = ref([])
const weeksAppts = ref([])
const weekPatients = ref([])

// jot down time windows the doctor can actually show up
const availRows = ref([{ date: '', start: '', end: '', fee: '' }])

function addRow() {
  availRows.value.push({ date: '', start: '', end: '', fee: '' })
}
function dropRow(i) {
  if (availRows.value.length > 1) {
    availRows.value.splice(i, 1)
  }
}

// save availability windows; nothing groundbreaking
async function saveAvailability() {
  try {
    const clean = availRows.value
      .filter(s => s.date && s.start && s.end)
      .map(s => ({
        date: s.date,
        start: s.start,
        end: s.end,
        fee: s.fee
      }))
    if (!clean.length) {
      alert('Add at least one slot with date, start and end.')
      return
    }
    await axios.post('/api/doctor/availability', clean, { headers: auth })
    alert('Saved!')
    // start fresh for the next batch
    availRows.value = [{ date: '', start: '', end: '', fee: '' }]
  } catch (err) {
    console.error(err)
    alert('Could not save availability.')
  }
}

// pull what matters for a quick glance
async function loadBoard() {
  problem.value = ''
  try {
    const { data } = await axios.get('/api/doctor/dashboard', { headers: auth })
    todaysAppts.value = data.today || []
    weeksAppts.value = data.week || []
    weekPatients.value = data.patients || []
  } catch (err) {
    console.error(err)
    problem.value = 'Failed to load doctor dashboard'
  }
}

const isRefreshing = ref(false)
async function refreshNow() {
  isRefreshing.value = true
  await loadBoard()
  isRefreshing.value = false
}

/* Mark a visit done and record notes */
const showTreat = ref(false)
const selected = ref(null)
const treatForm = ref({ diagnosis: '', prescription: '', notes: '', next_visit: '' })
const treatErr = ref('')
const treatOk = ref('')
const isEditing = ref(false)

function openTreat(appt) {
  selected.value = appt
  treatForm.value = { diagnosis: '', prescription: '', notes: '', next_visit: '' }
  treatErr.value = ''
  treatOk.value = ''
  isEditing.value = false
  showTreat.value = true
}

function editTreat(appt) {
  selected.value = appt
  const t = appt?.treatment || {}
  const nv = t?.next_visit ? String(t.next_visit).slice(0, 10) : ''
  treatForm.value = {
    diagnosis: t?.diagnosis || '',
    prescription: t?.prescription || '',
    notes: t?.notes || '',
    next_visit: nv
  }
  const hasExisting = !!(t && (t.diagnosis || t.prescription || t.notes || t.next_visit))
  treatErr.value = ''
  treatOk.value = ''
  isEditing.value = hasExisting
  showTreat.value = true
}
function closeTreat() {
  showTreat.value = false
  selected.value = null
}
async function submitTreat() {
  treatErr.value = ''
  treatOk.value = ''
  if (!treatForm.value.diagnosis) {
    treatErr.value = 'Diagnosis is required'
    return
  }
  try {
    const id = selected.value.id
    const method = isEditing.value ? 'put' : 'post'
    await axios[method](`/api/appointments/${id}/treatment`, treatForm.value, { headers: auth })
    treatOk.value = isEditing.value ? 'Treatment updated' : 'Saved and marked as Completed'
    setTimeout(async () => {
      closeTreat()
      if (who.value?.id) {
        await openHistory(who.value.id)
      } else {
        await loadBoard()
      }
    }, 300)
  } catch (err) {
    console.error(err)
    treatErr.value = err?.response?.data?.message || 'Could not save treatment'
  }
}

/* Cancel a booking if the patient can’t make it */
const isCancelling = ref(false)
async function cancelAppt(appt) {
  if (!confirm('Cancel this appointment?')) return
  try {
    isCancelling.value = true
    await axios.delete(`/api/appointments/${appt.id}`, { headers: auth })
    await loadBoard()
  } catch (err) {
    console.error(err)
    alert(err?.response?.data?.message || 'Failed to cancel appointment')
  } finally {
    isCancelling.value = false
  }
}

/* Quick look at this patient’s history with you */
const showHistory = ref(false)
const isHistoryBusy = ref(false)
const historyErr = ref('')
const who = ref(null)
const pastWithMe = ref([])

async function openHistory(patientId) {
  showHistory.value = true
  isHistoryBusy.value = true
  historyErr.value = ''
  who.value = null
  pastWithMe.value = []
  try {
    const { data } = await axios.get(`/api/doctor/patients/${patientId}/history`, { headers: auth })
    who.value = data.patient
    pastWithMe.value = data.appointments || []
  } catch (err) {
    console.error(err)
    historyErr.value = err?.response?.data?.message || 'Failed to load history'
  } finally {
    isHistoryBusy.value = false
  }
}
function closeHistory() {
  showHistory.value = false
  who.value = null
  pastWithMe.value = []
}

// boot
onMounted(async () => {
  isBusy.value = true
  await loadBoard()
  isBusy.value = false
})
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Doctor Dashboard</h2>
      <button class="btn btn-sm btn-outline-secondary" :disabled="isRefreshing" @click="refreshNow">
        {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="isBusy" class="alert alert-info">Loading...</div>
    <div v-else-if="problem" class="alert alert-danger">{{ problem }}</div>

    <div v-else>
      <div class="row g-4">
        <div class="col-12 col-lg-7">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Today's Appointments</h5>
              <div class="table-responsive">
                <table class="table table-sm table-striped align-middle">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Patient</th>
                      <th>Status</th>
                      <th>Reason</th>
                      <th class="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in todaysAppts" :key="a.id">
                      <td>{{ a.appointment_time }}</td>
                      <td>{{ a.patient_name }}</td>
                      <td>
                        <span :class="['badge', a.status === 'Booked' ? 'bg-info' : a.status === 'Completed' ? 'bg-success' : 'bg-secondary']">
                          {{ a.status }}
                        </span>
                      </td>
                      <td>{{ a.reason }}</td>
                      <td class="text-end">
                        <div class="btn-group btn-group-sm">
                          <button class="btn btn-success" :disabled="a.status !== 'Booked'" @click="openTreat(a)">Complete</button>
                          <button class="btn btn-outline-danger" :disabled="a.status !== 'Booked' || isCancelling" @click="cancelAppt(a)">Cancel</button>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!todaysAppts.length">
                      <td colspan="5" class="text-muted">No appointments today.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-5">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Patients (this week)</h5>
              <div class="row g-3">
                <div class="col-12" v-if="!weekPatients.length">
                  <div class="text-muted">No patients found for the week.</div>
                </div>
                <div class="col-12" v-for="p in weekPatients" :key="p.id">
                  <div class="card h-100">
                    <div class="card-body d-flex justify-content-between align-items-center">
                      <div>
                        <div class="fw-semibold">{{ p.name }}</div>
                        <div class="text-muted small">{{ p.email }}</div>
                        <div class="text-muted small">{{ p.phone }}</div>
                      </div>
                      <button class="btn btn-sm btn-outline-primary" @click="openHistory(p.id)">History</button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="form-text mt-2">Pick a patient to view their visit history. You can edit completed visits.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- changes done to make set availablitl -->
      <div class="card mb-3 mt-2">
        <div class="card-body">
          <h5 class="card-title">Add Availability (Next 7 days)</h5>
          <div class="small text-muted mb-2">Add time windows you’ll be available</div>

          <div v-for="(s, idx) in availRows" :key="idx" class="slot-card p-2 mb-2 border rounded">
            <div class="row g-3 align-items-end">
              <div class="col-12 col-md-4">
                <label class="form-label mb-1">Date</label>
                <input type="date" class="form-control" v-model="s.date" />
              </div>
              <div class="col-6 col-md-2">
                <label class="form-label mb-1">Start</label>
                <input type="time" class="form-control" v-model="s.start" />
              </div>
              <div class="col-6 col-md-2">
                <label class="form-label mb-1">End</label>
                <input type="time" class="form-control" v-model="s.end" />
              </div>
              <div class="col-6 col-md-3">
                <label class="form-label mb-1">Fee (₹)</label>
                <input type="number" min="0" step="1" placeholder="e.g. 500" class="form-control" v-model="s.fee" />
              </div>
              <div class="col-6 col-md-1 d-grid">
                <button class="btn btn-sm btn-outline-danger remove-btn" @click="dropRow(idx)" :disabled="availRows.length === 1">×</button>
              </div>
            </div>
          </div>

          <div class="d-flex flex-wrap gap-2">
            <button class="btn btn-sm btn-outline-secondary" @click="addRow">Add slot</button>
            <button class="btn btn-sm btn-primary" @click="saveAvailability">Save Availability</button>
          </div>
        </div>
      </div>

      <h5 class="mt-4">This Week's Appointments</h5>
      <div class="table-responsive">
        <table class="table table-sm table-hover align-middle">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Patient</th>
              <th>Status</th>
              <th>Reason</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in weeksAppts" :key="a.id">
              <td>{{ a.appointment_date }}</td>
              <td>{{ a.appointment_time }}</td>
              <td>{{ a.patient_name }}</td>
              <td>
                <span :class="['badge', a.status === 'Booked' ? 'bg-info' : a.status === 'Completed' ? 'bg-success' : 'bg-secondary']">{{ a.status }}</span>
              </td>
              <td>{{ a.reason }}</td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <button class="btn btn-success" :disabled="a.status !== 'Booked'" @click="openTreat(a)">Complete</button>
                  <button class="btn btn-outline-danger" :disabled="a.status !== 'Booked' || isCancelling" @click="cancelAppt(a)">Cancel</button>
                </div>
              </td>
            </tr>
            <tr v-if="!weeksAppts.length">
              <td colspan="6" class="text-muted">No appointments scheduled.</td>
            </tr>
          </tbody>
        </table>
      </div>


    </div>

    <!-- Treatment Modal -->
    <div v-if="showTreat" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? 'Edit Treatment' : 'Complete Appointment' }} - {{ selected?.patient_name }} ({{ selected?.appointment_date }} {{ selected?.appointment_time }})</h5>
            <button type="button" class="btn-close" @click="closeTreat"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitTreat">
              <div class="mb-2">
                <label class="form-label">Diagnosis</label>
                <textarea v-model="treatForm.diagnosis" class="form-control" rows="2" required></textarea>
              </div>
              <div class="mb-2">
                <label class="form-label">Prescription</label>
                <textarea v-model="treatForm.prescription" class="form-control" rows="2"></textarea>
              </div>
              <div class="mb-2">
                <label class="form-label">Notes</label>
                <textarea v-model="treatForm.notes" class="form-control" rows="2"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">Next Visit (optional)</label>
                <input type="date" class="form-control" v-model="treatForm.next_visit" />
              </div>
              <div v-if="treatErr" class="alert alert-danger">{{ treatErr }}</div>
              <div v-if="treatOk" class="alert alert-success">{{ treatOk }}</div>
              <div class="d-flex gap-2">
                <button class="btn btn-primary" type="submit">Save</button>
                <button class="btn btn-secondary" type="button" @click="closeTreat">Close</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- Patient History Modal -->
    <div v-if="showHistory" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Patient History - {{ who?.name }}</h5>
            <button type="button" class="btn-close" @click="closeHistory"></button>
          </div>
          <div class="modal-body">
            <div v-if="isHistoryBusy" class="alert alert-info">Loading...</div>
            <div v-else-if="historyErr" class="alert alert-danger">{{ historyErr }}</div>
            <div v-else>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Status</th>
                      <th>Diagnosis</th>
                      <th>Prescription</th>
                      <th class="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="h in pastWithMe" :key="h.id">
                      <td>{{ h.appointment_date }}</td>
                      <td>{{ h.appointment_time }}</td>
                      <td><span :class="['badge', h.status === 'Completed' ? 'bg-success' : h.status === 'Booked' ? 'bg-info' : 'bg-secondary']">{{ h.status }}</span></td>
                      <td>{{ h.treatment?.diagnosis || '' }}</td>
                      <td>{{ h.treatment?.prescription || '' }}</td>
                      <td class="text-end">
                        <button v-if="h.status === 'Completed'" class="btn btn-sm btn-outline-primary" @click="editTreat(h)">Edit</button>
                      </td>
                    </tr>
                    <tr v-if="!pastWithMe.length">
                      <td colspan="6" class="text-muted">No prior appointments found.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="d-flex justify-content-end">
              <button class="btn btn-secondary" @click="closeHistory">Close</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.container { max-width: 1100px; }
.modal { display: block; }

/* Availability layout polish */
.slot-card {
  background: #f8fafc;
  border-color: #e5e7eb;
  border-radius: 12px;
}
.remove-btn {
  margin-top: 0.5rem;
}
@media (max-width: 576px) {
  .slot-card .form-label { margin-bottom: 4px; }
  .remove-btn { margin-top: 0.25rem; }
}
</style>
