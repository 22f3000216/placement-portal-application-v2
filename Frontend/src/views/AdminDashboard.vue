<template>
  <div class="container mt-4">
    <h3>Admin Dashboard</h3>
    <div class="row mb-3">
      <div class="col"><div class="card p-2 text-center">Students<br><b>{{ stats.total_students }}</b></div></div>
      <div class="col"><div class="card p-2 text-center">Companies<br><b>{{ stats.total_companies }}</b></div></div>
      <div class="col"><div class="card p-2 text-center">Jobs<br><b>{{ stats.total_jobs }}</b></div></div>
      <div class="col"><div class="card p-2 text-center">Applications<br><b>{{ stats.total_applications }}</b></div></div>
    </div>

    <button class="btn btn-secondary btn-sm mb-3" @click="generateReport">Generate Monthly Report</button>
    <p class="text-success">{{ successMessage }}</p>
    <p class="text-danger">{{ message }}</p>

    <h5>Companies</h5>
    <input v-model="companySearch" @input="searchCompanies" class="form-control mb-2" placeholder="Search by name or industry...">
    <table class="table table-bordered table-sm">
      <thead><tr><th>Name</th><th>Industry</th><th>Approved</th><th>Rejected</th><th>Blocked</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="c in companies" :key="c.id">
          <td>{{ c.name }}</td><td>{{ c.industry }}</td><td>{{ c.is_approved }}</td>
          <td>{{ c.is_rejected }}</td><td>{{ c.is_blocked }}</td>
          <td>
            <button class="btn btn-sm btn-success me-1" @click="approveCompany(c.id)">Approve</button>
            <button class="btn btn-sm btn-secondary me-1" @click="rejectCompany(c.id)">Reject</button>
            <button v-if="!c.is_blocked" class="btn btn-sm btn-warning me-1" @click="blockCompany(c.id)">Block</button>
            <button v-else class="btn btn-sm btn-warning me-1" @click="unblockCompany(c.id)">Unblock</button>
            <button class="btn btn-sm btn-danger" @click="removeCompany(c.id)">Remove</button>
          </td>
        </tr>
      </tbody>
    </table>

    <h5>Students</h5>
    <input v-model="studentSearch" @input="searchStudents" class="form-control mb-2" placeholder="Search by name, ID or contact...">
    <table class="table table-bordered table-sm">
      <thead><tr><th>ID</th><th>Name</th><th>Contact</th><th>Degree</th><th>Branch</th><th>CGPA</th><th>Skills</th><th>Experience</th><th>Blocked</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="s in students" :key="s.id">
          <td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.contact }}</td><td>{{ s.degree }}</td>
          <td>{{ s.branch }}</td><td>{{ s.cgpa }}</td><td>{{ s.skills }}</td><td>{{ s.experience }}</td>
          <td>{{ s.is_blocked }}</td>
          <td>
            <button v-if="!s.is_blocked" class="btn btn-sm btn-warning" @click="blockStudent(s.id)">Block</button>
            <button v-else class="btn btn-sm btn-warning" @click="unblockStudent(s.id)">Unblock</button>
          </td>
        </tr>
      </tbody>
    </table>

    <h5>Pending Job Approvals</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Title</th><th>Company</th><th>Actions</th></tr></thead>
      <tbody>
        <tr v-for="j in pendingJobs" :key="j.id">
          <td>{{ j.title }}</td><td>{{ j.company_name }}</td>
          <td>
            <button class="btn btn-sm btn-success me-1" @click="approveJob(j.id)">Approve</button>
            <button class="btn btn-sm btn-secondary me-1" @click="rejectJob(j.id)">Reject</button>
            <button class="btn btn-sm btn-danger" @click="removeJob(j.id)">Remove</button>
          </td>
        </tr>
      </tbody>
    </table>

    <h5>All Job Postings</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Title</th><th>Company</th><th>Approved</th><th>Status</th><th>Applications</th><th>Action</th></tr></thead>
      <tbody>
        <tr v-for="j in allJobs" :key="j.id">
          <td>{{ j.title }}</td><td>{{ j.company_name }}</td><td>{{ j.is_approved }}</td>
          <td>{{ j.status }}</td><td>{{ j.application_count }}</td>
          <td><button class="btn btn-sm btn-danger" @click="removeJob(j.id)">Remove</button></td>
        </tr>
      </tbody>
    </table>

    <h5>All Applications</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Student</th><th>Job</th><th>Company</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>
        <tr v-for="a in allApplications" :key="a.id">
          <td>{{ a.student_name }}</td><td>{{ a.job_title }}</td><td>{{ a.company_name }}</td><td>{{ a.status }}</td>
          <td><button class="btn btn-sm btn-danger" @click="removeApplication(a.id)">Remove</button></td>
        </tr>
      </tbody>
    </table>

    <h5>Placements</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Student</th><th>Company</th><th>Position</th><th>Package</th></tr></thead>
      <tbody>
        <tr v-for="p in placements" :key="p.student_name + p.company_name">
          <td>{{ p.student_name }}</td><td>{{ p.company_name }}</td><td>{{ p.position }}</td><td>{{ p.package }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import api from "../api"

export default {
  data() {
    return {
      stats: {}, companies: [], students: [], pendingJobs: [], allJobs: [],
      allApplications: [], placements: [], companySearch: "", studentSearch: "",
      message: "", successMessage: ""
    }
  },
  async created() {
    await this.loadAll()
  },
  methods: {
    async loadAll() {
      this.stats = (await api.get("/admin/stats")).data
      this.companies = (await api.get("/admin/companies")).data
      this.students = (await api.get("/admin/students")).data
      this.pendingJobs = (await api.get("/admin/jobs/pending")).data
      this.allJobs = (await api.get("/admin/jobs")).data
      this.allApplications = (await api.get("/admin/applications")).data
      this.placements = (await api.get("/admin/placements")).data
    },
    async searchCompanies() {
      this.companies = (await api.get("/admin/companies", { params: { q: this.companySearch } })).data
    },
    async searchStudents() {
      this.students = (await api.get("/admin/students", { params: { q: this.studentSearch } })).data
    },
    async approveCompany(id) {
      try {
        const res = await api.put(`/admin/companies/${id}/approve`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async rejectCompany(id) {
      try {
        const res = await api.put(`/admin/companies/${id}/reject`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async blockCompany(id) {
      try {
        const res = await api.put(`/admin/companies/${id}/block`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async unblockCompany(id) {
      try {
        const res = await api.put(`/admin/companies/${id}/unblock`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async removeCompany(id) {
      try {
        const res = await api.delete(`/admin/companies/${id}`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async blockStudent(id) {
      try {
        const res = await api.put(`/admin/students/${id}/block`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async unblockStudent(id) {
      try {
        const res = await api.put(`/admin/students/${id}/unblock`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async approveJob(id) {
      try {
        const res = await api.put(`/admin/jobs/${id}/approve`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async rejectJob(id) {
      try {
        const res = await api.put(`/admin/jobs/${id}/reject`)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadAll()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async removeJob(id) { await api.delete(`/admin/jobs/${id}`); await this.loadAll() },
    async removeApplication(id) { await api.delete(`/admin/applications/${id}`); await this.loadAll() },

    async generateReport() {
      try {
        const res = await api.post("/admin/reports/generate")

        this.successMessage = res.data.message
        this.message = ""

      } catch (error) {

        this.message = error.response?.data?.message || "Failed to start report generation."
        this.successMessage = ""

      }
    
    }
  }
}
</script>
