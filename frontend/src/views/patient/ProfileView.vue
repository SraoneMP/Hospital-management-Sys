<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  name: '',
  email: '',
  phone: '',
  address: '',
  dob: '',
  gender: '',
  emergency_contact: ''
})

const fetchProfile = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get('/api/patient/profile', { headers: authHeader })
    const p = data.profile || {}
    form.value = {
      name: p.name || '',
      email: p.email || '',
      phone: p.phone || '',
      address: p.address || '',
      dob: p.dob || '',
      gender: p.gender || '',
      emergency_contact: p.emergency_contact || ''
    }
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

const saveProfile = async () => {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      phone: form.value.phone,
      address: form.value.address,
      dob: form.value.dob || null,
      gender: form.value.gender || null,
      emergency_contact: form.value.emergency_contact || null
    }
    await axios.put('/api/patient/profile', payload, { headers: authHeader })
    success.value = 'Profile updated successfully'
    // also keep localStorage user in sync for UI that reads it
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    user.name = form.value.name
    user.email = form.value.email
    localStorage.setItem('user', JSON.stringify(user))
  } catch (e) {
    console.error(e)
    error.value = e.response?.data?.message || 'Failed to update profile'
  } finally {
    saving.value = false
  }
}

onMounted(fetchProfile)
</script>

<template>
  <div class="container my-4">
    <h2 class="mb-3">My Profile</h2>

    <div v-if="loading" class="alert alert-info">Loading profile...</div>
    <div v-else>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="card">
        <div class="card-body">
          <form class="row g-3" @submit.prevent="saveProfile">
            <div class="col-md-6">
              <label class="form-label">Full Name</label>
              <input v-model="form.name" class="form-control" required />
            </div>
            <div class="col-md-6">
              <label class="form-label">Email</label>
              <input v-model="form.email" class="form-control" type="email" disabled />
            </div>
            <div class="col-md-6">
              <label class="form-label">Phone</label>
              <input v-model="form.phone" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Date of Birth</label>
              <input v-model="form.dob" type="date" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Gender</label>
              <select v-model="form.gender" class="form-select">
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">Emergency Contact</label>
              <input v-model="form.emergency_contact" class="form-control" placeholder="Name / Number" />
            </div>
            <div class="col-12">
              <label class="form-label">Address</label>
              <textarea v-model="form.address" class="form-control" rows="2"></textarea>
            </div>

            <div class="col-12 d-flex gap-2">
              <button class="btn btn-primary" type="submit" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save Changes' }}
              </button>
              <button class="btn btn-outline-secondary" type="button" @click="fetchProfile" :disabled="saving">Reset</button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.container { max-width: 900px; }
</style>
