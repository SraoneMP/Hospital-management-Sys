<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const doctors = ref([])
const total = ref(0)
const departments = ref([])

// filters
const filter = ref({
  q: '',
  department: '',
  active: '' // '', 'true', 'false'
})

const fetchDepartments = async () => {
  try {
    const { data } = await axios.get('/api/admin/departments', { headers: authHeader })
    departments.value = data.departments || []
  } catch (e) {
    console.error(e)
  }
}

const fetchDoctors = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (filter.value.q) params.q = filter.value.q
    if (filter.value.department) params.department = filter.value.department
    if (filter.value.active !== '') params.active = filter.value.active
    const { data } = await axios.get('/api/admin/doctors', { headers: authHeader, params })
    doctors.value = data.doctors || []
    total.value = data.total ?? doctors.value.length
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load doctors'
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  filter.value = { q: '', department: '', active: '' }
  await fetchDoctors()
}

// Add Doctor modal
const addModal = ref(false)
const addForm = ref({
  name: '',
  email: '',
  password: '',
  specialization: '',
  department_id: '',
  phone: '',
  address: '',
  bio: ''
})
const addError = ref('')
const addSuccess = ref('')

const openAdd = () => {
  addForm.value = { name: '', email: '', password: '', specialization: '', department_id: '', phone: '', address: '', bio: '' }
  addError.value = ''
  addSuccess.value = ''
  addModal.value = true
}
const closeAdd = () => { addModal.value = false }

const submitAdd = async () => {
  addError.value = ''
  addSuccess.value = ''
  if (!addForm.value.name || !addForm.value.email || !addForm.value.password || !addForm.value.specialization) {
    addError.value = 'Please fill required fields'
    return
  }
  try {
    const payload = {
      name: addForm.value.name,
      email: addForm.value.email,
      password: addForm.value.password,
      specialization: addForm.value.specialization,
      department_id: addForm.value.department_id || null,
      phone: addForm.value.phone || null,
      address: addForm.value.address || null,
      bio: addForm.value.bio || null
    }
    await axios.post('/api/admin/doctors', payload, { headers: authHeader })
    addSuccess.value = 'Doctor created successfully'
    setTimeout(async () => {
      closeAdd()
      await fetchDoctors()
    }, 800)
  } catch (e) {
    console.error(e)
    addError.value = e.response?.data?.message || 'Failed to create doctor'
  }
}

// Edit Doctor modal
const editModal = ref(false)
const editForm = ref({
  id: null,
  name: '',
  phone: '',
  address: '',
  specialization: '',
  department_id: '',
  bio: '',
  is_active: true
})
const editError = ref('')
const editSuccess = ref('')

const openEdit = (doc) => {
  editForm.value = {
    id: doc.id,
    name: doc.name || '',
    phone: doc.phone || '',
    address: doc.address || '',
    specialization: doc.specialization || '',
    department_id: departments.value.find(d => d.name === doc.department)?.id || '',
    bio: doc.bio || '',
    is_active: !!doc.is_active
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
      specialization: editForm.value.specialization,
      department_id: editForm.value.department_id || null,
      bio: editForm.value.bio,
      is_active: editForm.value.is_active
    }
    await axios.put(`/api/admin/doctors/${editForm.value.id}`, payload, { headers: authHeader })
    editSuccess.value = 'Doctor updated successfully'
    setTimeout(async () => {
      closeEdit()
      await fetchDoctors()
    }, 800)
  } catch (e) {
    console.error(e)
    editError.value = e.response?.data?.message || 'Failed to update doctor'
  }
}

// Deactivate doctor (blacklist)
const deactivate = async (doc) => {
  if (!confirm(`Deactivate doctor ${doc.name}?`)) return
  try {
    await axios.delete(`/api/admin/doctors/${doc.id}`, { headers: authHeader })
    await fetchDoctors()
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.message || 'Failed to deactivate doctor')
  }
}

onMounted(async () => {
  await fetchDepartments()
  await fetchDoctors()
})
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Manage Doctors</h2>
      <button class="btn btn-sm btn-success" @click="openAdd">Add Doctor</button>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <form class="row g-2 align-items-end" @submit.prevent="fetchDoctors">
          <div class="col-12 col-md-4">
            <label class="form-label">Search</label>
            <input v-model="filter.q" class="form-control" placeholder="Name / Email / Phone / Specialization" />
          </div>
          <div class="col-6 col-md-3">
            <label class="form-label">Department</label>
            <select v-model="filter.department" class="form-select">
              <option value="">All</option>
              <option v-for="d in departments" :key="d.id" :value="d.name">{{ d.name }}</option>
            </select>
          </div>
          <div class="col-6 col-md-3">
            <label class="form-label">Status</label>
            <select v-model="filter.active" class="form-select">
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
          <div class="col-12 col-md-2 d-grid">
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
                  <th>Specialization</th>
                  <th>Department</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="doc in doctors" :key="doc.id">
                  <td>{{ doc.name }}</td>
                  <td>{{ doc.specialization }}</td>
                  <td>{{ doc.department || '-' }}</td>
                  <td>{{ doc.phone || '-' }}</td>
                  <td>
                    <span :class="['badge', doc.is_active ? 'bg-success' : 'bg-secondary']">{{ doc.is_active ? 'Active' : 'Inactive' }}</span>
                  </td>
                  <td class="text-end">
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="openEdit(doc)">Edit</button>
                      <button class="btn btn-outline-danger" @click="deactivate(doc)" :disabled="!doc.is_active">Deactivate</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!doctors.length">
                  <td colspan="6" class="text-muted">No doctors found.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="small text-muted mt-2">Total: {{ total }}</div>
        </div>
      </div>
    </div>

    <!-- Add Doctor Modal -->
    <div v-if="addModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add Doctor</h5>
            <button type="button" class="btn-close" @click="closeAdd"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitAdd" class="row g-2">
              <div class="col-md-6">
                <label class="form-label">Name</label>
                <input v-model="addForm.name" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Email</label>
                <input v-model="addForm.email" type="email" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Password</label>
                <input v-model="addForm.password" type="password" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Specialization</label>
                <input v-model="addForm.specialization" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Department</label>
                <select v-model="addForm.department_id" class="form-select">
                  <option value="">Select...</option>
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">Phone</label>
                <input v-model="addForm.phone" class="form-control" />
              </div>
              <div class="col-12">
                <label class="form-label">Address</label>
                <input v-model="addForm.address" class="form-control" />
              </div>
              <div class="col-12">
                <label class="form-label">Bio</label>
                <textarea v-model="addForm.bio" class="form-control" rows="2"></textarea>
              </div>

              <div v-if="addError" class="alert alert-danger">{{ addError }}</div>
              <div v-if="addSuccess" class="alert alert-success">{{ addSuccess }}</div>

              <div class="d-flex gap-2">
                <button class="btn btn-primary" type="submit">Create</button>
                <button class="btn btn-secondary" type="button" @click="closeAdd">Close</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Doctor Modal -->
    <div v-if="editModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Doctor</h5>
            <button type="button" class="btn-close" @click="closeEdit"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitEdit" class="row g-2">
              <div class="col-md-6">
                <label class="form-label">Name</label>
                <input v-model="editForm.name" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Phone</label>
                <input v-model="editForm.phone" class="form-control" />
              </div>
              <div class="col-md-6">
                <label class="form-label">Specialization</label>
                <input v-model="editForm.specialization" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label">Department</label>
                <select v-model="editForm.department_id" class="form-select">
                  <option value="">Select...</option>
                  <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </div>
              <div class="col-12">
                <label class="form-label">Address</label>
                <input v-model="editForm.address" class="form-control" />
              </div>
              <div class="col-12">
                <label class="form-label">Bio</label>
                <textarea v-model="editForm.bio" class="form-control" rows="2"></textarea>
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
            <div class="form-text mt-2">
              Note: Deactivating a doctor prevents new appointments and hides them from patient search.
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
</style>
