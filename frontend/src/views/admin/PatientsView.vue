<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const patients = ref([])
const total = ref(0)

// filters
const filter = ref({
  q: '',
  active: '' // '', 'true', 'false'
})

const fetchPatients = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (filter.value.q) params.q = filter.value.q
    if (filter.value.active !== '') params.active = filter.value.active
    const { data } = await axios.get('/api/admin/patients', { headers: authHeader, params })
    patients.value = data.patients || []
    total.value = data.total ?? patients.value.length
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load patients'
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  filter.value = { q: '', active: '' }
  await fetchPatients()
}

// Edit Patient modal
const editModal = ref(false)
const editForm = ref({
  id: null,
  name: '',
  email: '',
  phone: '',
  address: '',
  dob: '',
  gender: '',
  emergency_contact: '',
  is_active: true
})
const editError = ref('')
const editSuccess = ref('')

const openEdit = (p) => {
  editForm.value = {
    id: p.id,
    name: p.name || '',
    email: p.email || '',
    phone: p.phone || '',
    address: p.address || '',
    dob: p.dob || '',
    gender: p.gender || '',
    emergency_contact: p.emergency_contact || '',
    is_active: !!p.is_active
  }
  editError.value = ''
  editSuccess.value = ''
  editModal.value = true
}
const closeEdit = () => { editModal.value = false }

const submitEdit = async () => {
  editError.value = ''
  editSuccess.value = ''
  if (!editForm.value.id) return
  try {
    const payload = {
      name: editForm.value.name,
      phone: editForm.value.phone,
      address: editForm.value.address,
      dob: editForm.value.dob || null,
      gender: editForm.value.gender || null,
      emergency_contact: editForm.value.emergency_contact || null,
      is_active: editForm.value.is_active
    }
    await axios.put(`/api/admin/patients/${editForm.value.id}`, payload, { headers: authHeader })
    editSuccess.value = 'Patient updated successfully'
    setTimeout(async () => {
      closeEdit()
      await fetchPatients()
    }, 800)
  } catch (e) {
    console.error(e)
    editError.value = e.response?.data?.message || 'Failed to update patient'
  }
}

// Deactivate patient (blacklist)
const deactivate = async (p) => {
  if (!confirm(`Deactivate patient ${p.name}?`)) return
  try {
    await axios.delete(`/api/admin/patients/${p.id}`, { headers: authHeader })
    await fetchPatients()
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.message || 'Failed to deactivate patient')
  }
}

onMounted(fetchPatients)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Manage Patients</h2>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <form class="row g-2 align-items-end" @submit.prevent="fetchPatients">
          <div class="col-12 col-md-6">
            <label class="form-label">Search</label>
            <input v-model="filter.q" class="form-control" placeholder="Name / Email / Phone" />
          </div>
          <div class="col-6 col-md-3">
            <label class="form-label">Status</label>
            <select v-model="filter.active" class="form-select">
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
          <div class="col-6 col-md-3 d-grid">
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

      <div class="card">
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-sm table-striped align-middle">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>DOB</th>
                  <th>Gender</th>
                  <th>Status</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in patients" :key="p.id">
                  <td>{{ p.name }}</td>
                  <td>{{ p.email }}</td>
                  <td>{{ p.phone || '-' }}</td>
                  <td>{{ p.dob || '-' }}</td>
                  <td>{{ p.gender || '-' }}</td>
                  <td>
                    <span :class="['badge', p.is_active ? 'bg-success' : 'bg-secondary']">{{ p.is_active ? 'Active' : 'Inactive' }}</span>
                  </td>
                  <td class="text-end">
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="openEdit(p)">Edit</button>
                      <button class="btn btn-outline-danger" @click="deactivate(p)" :disabled="!p.is_active">Deactivate</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!patients.length">
                  <td colspan="7" class="text-muted">No patients found.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="small text-muted mt-2">Total: {{ total }}</div>
        </div>
      </div>
    </div>

    <!-- Edit Patient Modal -->
    <div v-if="editModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Patient</h5>
            <button type="button" class="btn-close" @click="closeEdit"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitEdit" class="row g-2">
              <div class="col-md-6">
                <label class="form-label">Name</label>
                <input v-model="editForm.name" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Email</label>
                <input v-model="editForm.email" class="form-control" type="email" disabled />
              </div>
              <div class="col-md-6">
                <label class="form-label">Phone</label>
                <input v-model="editForm.phone" class="form-control" />
              </div>
              <div class="col-md-6">
                <label class="form-label">DOB</label>
                <input v-model="editForm.dob" type="date" class="form-control" />
              </div>
              <div class="col-md-6">
                <label class="form-label">Gender</label>
                <select v-model="editForm.gender" class="form-select">
                  <option value="">Select...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">Emergency Contact</label>
                <input v-model="editForm.emergency_contact" class="form-control" />
              </div>
              <div class="col-12">
                <label class="form-label">Address</label>
                <input v-model="editForm.address" class="form-control" />
              </div>
              <div class="col-12">
                <div class="form-check">
                  <input id="activeCheck" class="form-check-input" type="checkbox" v-model="editForm.is_active" />
                  <label class="form-check-label" for="activeCheck">Active</label>
                </div>
              </div>

              <div v-if="editError" class="alert alert-danger">{{ editError }}</div>
              <div v-if="editSuccess" class="alert alert-success">{{ editSuccess }}</div>

              <div class="d-flex gap-2">
                <button class="btn btn-primary" type="submit">Save</button>
                <button class="btn btn-secondary" type="button" @click="closeEdit">Close</button>
              </div>
            </form>
            <div class="form-text mt-2">Note: Deactivating a patient prevents login and booking.</div>
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
