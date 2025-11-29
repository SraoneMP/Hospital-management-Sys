<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = ref({
  prime_location_name: '',
  address: '',
  price: '',
  pin_code: '',
  number_of_spots: ''
})

const error = ref('')
const success = ref('')

const submitLot = async () => {
  error.value = ''
  success.value = ''

  try {
    const res = await axios.post('http://localhost:5000/api/parkinglot', {
      ...form.value,
      price: parseFloat(form.value.price),
      number_of_spots: parseInt(form.value.number_of_spots)
    })

    success.value = 'Parking lot created successfully!'
    setTimeout(() => {
      router.push({ name: 'adminhome' })
    }, 1000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to create parking lot'
  }
}
</script>

<template>
  <div class="add-lot-container">
    <h2>Add New Parking Lot</h2>

    <form @submit.prevent="submitLot">
      <div class="form-group">
        <label>Prime Location Name</label>
        <input v-model="form.prime_location_name" required />
      </div>
      <div class="form-group">
        <label>Address</label>
        <textarea v-model="form.address" required></textarea>
      </div>
      <div class="form-group">
        <label>Price per Hour</label>
        <input type="number" step="0.01" v-model="form.price" required />
      </div>
      <div class="form-group">
        <label>Pin Code</label>
        <input v-model="form.pin_code" required />
      </div>
      <div class="form-group">
        <label>Total Number of Spots</label>
        <input type="number" v-model="form.number_of_spots" required />
      </div>

      <button type="submit">Create Parking Lot</button>

      <p class="success" v-if="success">{{ success }}</p>
      <p class="error" v-if="error">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.add-lot-container {
  padding: 30px;
  max-width: 600px;
  margin: auto;
}

form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group label {
  font-weight: bold;
}

input, textarea {
  width: 100%;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
}

button {
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

.success {
  color: green;
}

.error {
  color: red;
}
</style>
