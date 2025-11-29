<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Book an Appointment</h2>
      <router-link to="/patient/appointments" class="btn btn-sm btn-outline-primary">My Appointments</router-link>
    </div>

    <!-- search panel -->
    <div class="card mb-4">
      <div class="card-body">
        <form class="row g-3 align-items-end" @submit.prevent="findDoctors">
          <div class="col-12 col-md-3">
            <label class="form-label">Specialization</label>
            <input v-model="query.specialization" class="form-control" placeholder="e.g. Cardiology" />
          </div>
          <div class="col-12 col-md-3">
            <label class="form-label">Doctor Name</label>
            <input v-model="query.name" class="form-control" placeholder="Doctor name" />
          </div>
          <div class="col-6 col-md-2">
            <label class="form-label">Date</label>
            <input v-model="query.date" type="date" class="form-control" />
          </div>
          <div class="col-6 col-md-2">
            <label class="form-label">Time</label>
            <input v-model="query.time" type="time" class="form-control" />
          </div>
          <div class="col-12 col-md-2 d-grid">
            <button class="btn btn-primary" type="submit" :disabled="isBusy">{{ isBusy ? 'Searching...' : 'Search' }}</button>
          </div>
        </form>
        <div v-if="oops" class="alert alert-danger mt-3 mb-0">{{ oops }}</div>
      </div>
    </div>

    <!-- results -->
    <div class="card" v-if="foundDocs.length">
      <div class="card-body">
        <h5 class="mb-3">Available Doctors ({{ foundDocs.length }})</h5>
        <div class="table-container">
          <div class="table-responsive">
            <table class="table table-sm table-hover align-middle mb-0">
              <thead class="table-header-sticky">
                <tr>
                  <th>Name</th>
                  <th>Specialization</th>
                  <th>Department</th>
                  <th>Phone</th>
                  <th class="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="doc in foundDocs" :key="doc.id">
                  <td>{{ doc.name }}</td>
                  <td>{{ doc.specialization }}</td>
                  <td>{{ doc.department || '-' }}</td>
                  <td>{{ doc.phone || '-' }}</td>
                  <td class="text-end">
                    <button class="btn btn-sm btn-primary" @click="showBookSheet(doc)">Book</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="!foundDocs.length" class="text-muted small">No doctors found for selected criteria.</div>
      </div>
    </div>

    <!-- book modal -->
    <div v-if="showSheet" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Book with {{ chosenDoc?.name }}</h5>
            <button type="button" class="btn-close" @click="closeSheet"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="placeBooking" class="row g-3">
              <div class="col-12">
                <label class="form-label">Select Available Slot</label>
                <div v-if="slotBusy" class="text-muted">Loading slots...</div>
                <div v-else-if="openSlots.length" class="slot-grid mb-2">
                  <button
                    v-for="s in openSlots"
                    :key="s.id"
                    type="button"
                    :class="['btn', 'slot-btn', pick.slotKey === s.id ? 'btn-primary' : 'btn-outline-primary']"
                    @click="pickSlot(s)"
                  >
                    <div class="d-flex flex-column align-items-start">
                      <span class="fw-bold">{{ s.available_date }}</span>
                      <span class="small">{{ s.start_time }} - {{ s.end_time }}</span>
                      <span v-if="s.fee" class="small text-muted">₹{{ s.fee }}</span>
                    </div>
                  </button>
                </div>
                <div v-else class="text-danger">No available slots for this doctor.</div>
              </div>

              <div class="col-12">
                <label class="form-label">Reason (optional)</label>
                <input v-model="pick.note" class="form-control" placeholder="Short note" />
              </div>

              <div class="col-12" v-if="bookErr">
                <div class="alert alert-danger">{{ bookErr }}</div>
              </div>
              <div class="col-12" v-if="bookOk">
                <div class="alert alert-success">{{ bookOk }}</div>
              </div>

              <div class="col-12 d-flex gap-2 justify-content-end">
                <button class="btn btn-primary" type="submit" :disabled="bookBusy || !pick.slotKey">
                  {{ bookBusy ? 'Booking...' : 'Book' }}
                </button>
                <button class="btn btn-secondary" type="button" @click="closeSheet">Close</button>
              </div>
            </form>

            <div class="form-text mt-2">
              Tip: Only open slots appear here. Pick one and confirm.
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

// token goes in every request; keep it simple
const tokenRaw = localStorage.getItem('token') || ''
const auth = { Authorization: `Bearer ${tokenRaw}` }

// search state
const query = ref({ specialization: '', name: '', date: '', time: '' })
const isBusy = ref(false)
const oops = ref('')
const foundDocs = ref([])

// booking state
const showSheet = ref(false)
const chosenDoc = ref(null)
const pick = ref({ slotKey: null, date: '', time: '', note: '' })
const openSlots = ref([])
const slotBusy = ref(false)
const bookErr = ref('')
const bookOk = ref('')
const bookBusy = ref(false)

// pull dept/specialization from URL if present and auto search
const route = useRoute()
onMounted(() => {
  const q = route?.query || {}
  if (q.specialization) query.value.specialization = String(q.specialization)
  if (q.specialization || q.department) {
    findDoctors()
  }
})

// ping the backend to list doctors matching filters
async function findDoctors() {
  isBusy.value = true
  oops.value = ''
  foundDocs.value = []
  try {
    const params = {}
    if (query.value.specialization) params.specialization = query.value.specialization
    if (query.value.name) params.name = query.value.name
    if (query.value.date) params.date = query.value.date
    if (query.value.time) params.time = query.value.time
    // if we came via a department tile click
    if (route.query?.department) params.department = route.query.department

    const { data } = await axios.get('/api/doctors/search', { headers: auth, params })
    foundDocs.value = data.doctors || []
  } catch (err) {
    oops.value = err?.response?.data?.message || 'Search failed'
  } finally {
    isBusy.value = false
  }
}

// open modal and fetch slots for the picked doctor (respect date filter if any)
async function showBookSheet(doc) {
  chosenDoc.value = doc
  pick.value = { slotKey: null, date: '', time: '', note: '' }
  bookErr.value = ''
  bookOk.value = ''
  showSheet.value = true

  slotBusy.value = true
  openSlots.value = []
  try {
    const { data } = await axios.get(`/api/doctors/${doc.id}/slots`, {
      headers: auth,
      params: { date: query.value.date || undefined }
    })
    openSlots.value = data.slots || []
    // try "next available" if a specific date had nothing
    if ((!openSlots.value || !openSlots.value.length) && query.value.date) {
      const later = await axios.get(`/api/doctors/${doc.id}/slots`, { headers: auth })
      openSlots.value = later.data?.slots || []
    }
  } catch (_err) {
    openSlots.value = []
  } finally {
    slotBusy.value = false
  }
}

function closeSheet() {
  showSheet.value = false
  chosenDoc.value = null
  pick.value = { slotKey: null, date: '', time: '', note: '' }
  bookErr.value = ''
  bookOk.value = ''
  openSlots.value = []
}

function pickSlot(s) {
  pick.value.slotKey = s.id
  pick.value.date = s.available_date
  pick.value.time = s.start_time
}

// send booking to backend; the backend enforces availability+uniqueness
async function placeBooking() {
  bookErr.value = ''
  bookOk.value = ''
  if (!pick.value.slotKey || !pick.value.date || !pick.value.time) {
    bookErr.value = 'Please select a slot.'
    return
  }
  try {
    bookBusy.value = true
    const payload = {
      doctor_id: chosenDoc.value.id,
      date: pick.value.date,
      time: pick.value.time,
      reason: pick.value.note
    }
    await axios.post('/api/appointments', payload, { headers: auth })
    bookOk.value = 'Appointment booked!'
    setTimeout(() => {
      closeSheet()
    }, 1200)
  } catch (err) {
    bookErr.value = err?.response?.data?.message || 'Booking failed'
  } finally {
    bookBusy.value = false
  }
}
</script>

<style scoped>
.modal { display: block; }

.table-container {
  max-height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.table-header-sticky {
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.slot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.slot-btn {
  min-width: 150px;
  padding: 12px;
  text-align: left;
  transition: all 0.2s;
}

.slot-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.slot-btn.btn-primary {
  background: #6366f1;
  border-color: #6366f1;
  color: white;
}
</style>
