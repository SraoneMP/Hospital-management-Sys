<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')
const departments = ref([])

const fetchDepartments = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/admin/departments', { headers: authHeader })
    departments.value = data.departments || []
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load departments'
  } finally {
    loading.value = false
  }
}

// Add Department modal
const addModal = ref(false)
const addForm = ref({ name: '', description: '' })
const addError = ref('')
const addSuccess = ref('')

const openAdd = () => {
  addForm.value = { name: '', description: '' }
  addError.value = ''
  addSuccess.value = ''
  addModal.value = true
}
const closeAdd = () => { addModal.value = false }

const submitAdd = async () => {
  addError.value = ''
  addSuccess.value = ''
  if (!addForm.value.name) {
    addError.value = 'Department name is required'
    return
  }
  try {
    await axios.post('/api/admin/departments', addForm.value, { headers: authHeader })
    addSuccess.value = 'Department created successfully'
    setTimeout(async () => {
      closeAdd()
      await fetchDepartments()
    }, 800)
  } catch (e) {
    console.error(e)
    addError.value = e.response?.data?.message || 'Failed to create department'
  }
}

// Edit Department modal
const editModal = ref(false)
const editForm = ref({ id: null, name: '', description: '' })
const editError = ref('')
const editSuccess = ref('')

const openEdit = (dept) => {
  editForm.value = { id: dept.id, name: dept.name, description: dept.description || '' }
  editError.value = ''
  editSuccess.value = ''
  editModal.value = true
}
const closeEdit = () => { editModal.value = false }

const submitEdit = async () => {
  editError.value = ''
  editSuccess.value = ''
  if (!editForm.value.name) {
    editError.value = 'Department name is required'
    return
  }
  try {
    await axios.put(`/api/admin/departments/${editForm.value.id}`, {
      name: editForm.value.name,
      description: editForm.value.description
    }, { headers: authHeader })
    editSuccess.value = 'Department updated successfully'
    setTimeout(async () => {
      closeEdit()
      await fetchDepartments()
    }, 800)
  } catch (e) {
    console.error(e)
    editError.value = e.response?.data?.message || 'Failed to update department'
  }
}

// Delete Department
const deleteDept = async (dept) => {
  if (!confirm(`Delete department "${dept.name}"? This may affect doctor assignments.`)) return
  try {
    await axios.delete(`/api/admin/departments/${dept.id}`, { headers: authHeader })
    await fetchDepartments()
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.message || 'Failed to delete department')
  }
}

onMounted(fetchDepartments)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Manage Departments</h2>
      <button class="btn btn-sm btn-success" @click="openAdd">Add Department</button>
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
                  <th>Description</th>
                  <th>Doctors Registered</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dept in departments" :key="dept.id">
                  <td class="fw-semibold">{{ dept.name }}</td>
                  <td>{{ dept.description || '-' }}</td>
                  <td>{{ dept.doctors_registered }}</td>
                  <td class="text-end">
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="openEdit(dept)">Edit</button>
                      <button class="btn btn-outline-danger" @click="deleteDept(dept)">Delete</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!departments.length">
                  <td colspan="4" class="text-muted">No departments found.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Department Modal -->
    <div v-if="addModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add Department</h5>
            <button type="button" class="btn-close" @click="closeAdd"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitAdd">
              <div class="mb-2">
                <label class="form-label">Name</label>
                <input v-model="addForm.name" class="form-control" required />
              </div>
              <div class="mb-2">
                <label class="form-label">Description</label>
                <textarea v-model="addForm.description" class="form-control" rows="2"></textarea>
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

    <!-- Edit Department Modal -->
    <div v-if="editModal" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.3)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Department</h5>
            <button type="button" class="btn-close" @click="closeEdit"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitEdit">
              <div class="mb-2">
                <label class="form-label">Name</label>
                <input v-model="editForm.name" class="form-control" required />
              </div>
              <div class="mb-2">
                <label class="form-label">Description</label>
                <textarea v-model="editForm.description" class="form-control" rows="2"></textarea>
              </div>

              <div v-if="editError" class="alert alert-danger">{{ editError }}</div>
              <div v-if="editSuccess" class="alert alert-success">{{ editSuccess }}</div>

              <div class="d-flex gap-2">
                <button class="btn btn-primary" type="submit">Save</button>
                <button class="btn btn-secondary" type="button" @click="closeEdit">Close</button>
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
