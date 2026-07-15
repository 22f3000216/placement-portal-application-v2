<template>
  <div class="container mt-5" style="max-width: 400px;">
    <h3>Login</h3>
    <form @submit.prevent="handleLogin">
      <input v-model="email" 
        type="email" 
        required 
        class="form-control mb-2" 
        placeholder="Email">
      <input 
        v-model="password" 
        type="password" 
        required 
        minlength="6" 
        class="form-control mb-2" 
        placeholder="Password">
      <button type="submit" class="btn btn-primary w-100">
        Login
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
      email: "", 
      password: "", 
      message: "" 
    }
  },
  methods: {
    async handleLogin() {
      try {
        const response = await api.post("/auth/login", {
          email: this.email,
          password: this.password
        })
        localStorage.setItem("token", response.data.access_token)
        localStorage.setItem("role", response.data.role)

        if (response.data.role === "admin") this.$router.push("/admin")
        if (response.data.role === "company") this.$router.push("/company")
        if (response.data.role === "student") this.$router.push("/student")
      } catch (error) {
        this.message = error.response?.data?.message || "Invalid email or password"
      }
    }
  }
}
</script>
