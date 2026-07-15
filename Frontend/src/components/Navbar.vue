<template>
  <nav class="navbar navbar-dark bg-dark px-3">
    <span class="navbar-brand">Placement Portal</span>
    <div>
      <router-link to="/" class="btn btn-outline-light btn-sm me-2">Home</router-link>
      <router-link v-if="!isLoggedIn" to="/login" class="btn btn-outline-light btn-sm me-2">Login</router-link>
      <router-link v-if="!isLoggedIn" to="/register" class="btn btn-outline-light btn-sm">Register</router-link>
      <button v-if="isLoggedIn" class="btn btn-outline-light btn-sm" @click="logout">Logout ({{ role }})</button>
    </div>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      isLoggedIn: !!localStorage.getItem("token"),
      role: localStorage.getItem("role")
    }
  },
  mounted() {
    window.addEventListener("storage", this.refreshAuthState)
  },
  beforeUnmount() {
    window.removeEventListener("storage", this.refreshAuthState)
  },
  watch: {
    "$route"() {
      this.refreshAuthState()
    }
  },
  methods: {
    refreshAuthState() {
      this.isLoggedIn = !!localStorage.getItem("token")
      this.role = localStorage.getItem("role")
    },
    logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("role")
      this.refreshAuthState()
      this.$router.push("/login")
    }
  }
}
</script>
