import { createRouter, createWebHistory } from "vue-router"
import Landing from "../views/Landing.vue"
import Login from "../views/Login.vue"
import Register from "../views/Register.vue"
import AdminDashboard from "../views/AdminDashboard.vue"
import CompanyDashboard from "../views/CompanyDashboard.vue"
import StudentDashboard from "../views/StudentDashboard.vue"

const routes = [
  { path: "/", component: Landing },
  { path: "/login", component: Login },
  { path: "/register", component: Register },
  { path: "/admin", component: AdminDashboard },
  { path: "/company", component: CompanyDashboard },
  { path: "/student", component: StudentDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
