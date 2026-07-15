<template>
  <div class="container mt-5" style="max-width: 450px;">
    <h3>Register</h3>
    <form @submit.prevent="handleRegister">
    <input v-model="name" required class="form-control mb-2" placeholder="Name">
    <input v-model="email" type="email" required class="form-control mb-2" placeholder="Email">
    <input v-model="password" type="password" required minlength="6" class="form-control mb-2" placeholder="Password (min 6 characters)">
    <select v-model="role" class="form-control mb-2">
      <option value="student">Student</option>
      <option value="company">Company</option>
    </select>

    <div v-if="role === 'student'">
      <input v-model="degree" class="form-control mb-2" placeholder="Degree (e.g. B.Tech)">
      <input v-model="branch" class="form-control mb-2" placeholder="Branch (e.g. Computer Science)">
      <input v-model="year" class="form-control mb-2" placeholder="Year (e.g. 2026 or Final Year)">
      <input v-model="contact" class="form-control mb-2" placeholder="Contact Number">
      <input v-model="cgpa" type="number" step="0.01" min="0" max="10" class="form-control mb-2" placeholder="CGPA (0-10)">
      <input v-model="skills" class="form-control mb-2" placeholder="Skills (comma separated)">
      <input v-model="experience" class="form-control mb-2" placeholder="Experience (e.g. Fresher)">
    </div>

    <div v-if="role === 'company'">
      <input v-model="industry" class="form-control mb-2" placeholder="Industry">
      <input v-model="location" class="form-control mb-2" placeholder="Location">
      <input v-model="hr_contact" class="form-control mb-2" placeholder="HR Contact">
      <input v-model="website" class="form-control mb-2" placeholder="Company Website">
      <textarea v-model="about" class="form-control mb-2" placeholder="About your company"></textarea>
    </div>

    <button type="submit" class="btn btn-primary w-100">
      Register
    </button>
    </form>
    <p class="text-danger mt-2">{{ message }}</p>
  </div>
</template>

<script>
import api from "../api"

export default {
  data() {
    return {
      name: "", email: "", password: "", role: "student",
      branch: "", contact: "", cgpa: "", skills: "", experience: "", degree: "", year: "",
      industry: "", location: "", about: "", hr_contact: "", website: "",
      message: ""
    }
  },
  methods: {
    async handleRegister() {
      try {
        await api.post("/auth/register", {
          name: this.name, email: this.email, password: this.password, role: this.role,
          branch: this.branch, contact: this.contact, cgpa: this.cgpa, skills: this.skills,
          experience: this.experience, degree: this.degree, year: this.year,
          industry: this.industry, location: this.location, about: this.about,
          hr_contact: this.hr_contact, website: this.website
        })
        this.$router.push("/login")
      } catch (error) {
        this.message = error.response?.data?.message || "Registration failed"
      }
    }
  }
}
</script>
