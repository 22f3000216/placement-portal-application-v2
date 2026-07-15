<template>
  <div class="container mt-4">
    <h3>Student Dashboard</h3>

    <h5>My Profile</h5>
    <input v-model="studentProfileForm.name" class="form-control mb-2" placeholder="Name">
    <input v-model="studentProfileForm.degree" class="form-control mb-2" placeholder="Degree">
    <input v-model="studentProfileForm.branch" class="form-control mb-2" placeholder="Branch">
    <input v-model="studentProfileForm.year" class="form-control mb-2" placeholder="Year">
    <input v-model="studentProfileForm.contact" class="form-control mb-2" placeholder="Contact">
    <input v-model="studentProfileForm.cgpa" type="number" step="0.01" min="0" max="10" class="form-control mb-2" placeholder="CGPA">
    <input v-model="studentProfileForm.skills" class="form-control mb-2" placeholder="Skills">
    <input v-model="studentProfileForm.experience" class="form-control mb-2" placeholder="Experience">
    <label class="form-label">Upload Resume (PDF)</label>

    <input
      type="file"
      class="form-control mb-2"
      accept=".pdf"
      @change="selectedResume = $event.target.files[0]"
    >

    <button
      class="btn btn-outline-success mb-3"
      @click="uploadResume"
    >
      Upload Resume
    </button>

    <button class="btn btn-outline-primary mb-4" @click="saveStudentProfile">Save Profile</button>
    <p class="text-success">{{ successMessage }}</p>
    <p class="text-danger">{{ message }}</p>
    <button class="btn btn-secondary btn-sm mb-2" @click="exportCsv">Export My Applications as CSV</button>
    <button v-if="exportReady" class="btn btn-success btn-sm mb-2 ms-2" @click="downloadExportCsv">Download CSV</button>
    <button class="btn btn-outline-success btn-sm mb-2 ms-2" @click="downloadOfferLetter">Download Offer Letter</button>
    <p class="text-success">{{ exportMessage }}</p>

    <h5>Search Jobs</h5>
    <input v-model="jobSearch" @input="searchJobs" class="form-control mb-2" placeholder="Search by title, skills or company...">
    <div class="form-check mb-2">
      <input type="checkbox" v-model="eligibleOnly" @change="searchJobs" class="form-check-input" id="eligibleOnlyCheck">
      <label class="form-check-label" for="eligibleOnlyCheck">Show only drives I'm eligible for</label>
    </div>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Title</th><th>Company</th><th>Salary</th><th>Skills</th><th>Deadline</th><th>Eligible?</th><th>Action</th></tr></thead>
      <tbody>
        <tr v-for="j in openJobs" :key="j.id">
          <td>{{ j.title }}</td><td>{{ j.company_name }}</td><td>{{ j.salary }}</td>
          <td>{{ j.skills_required }}</td><td>{{ j.application_deadline }}</td>
          <td>
            <span v-if="j.is_eligible" class="text-success">Yes</span>
            <span v-else class="text-danger" :title="j.eligibility_reason">No</span>
          </td>
          <td><button class="btn btn-sm btn-primary" :disabled="!j.is_eligible" @click="applyJob(j.id)">Apply</button></td>
        </tr>
      </tbody>
    </table>

    <h5>My Applications</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Job</th><th>Company</th><th>Status</th><th>Interview Time</th><th>Feedback</th><th>Action</th></tr></thead>
      <tbody>
        <tr v-for="a in myApplications" :key="a.id">
          <td>{{ a.job_title }}</td><td>{{ a.company_name }}</td><td>{{ a.status }}</td>
          <td>{{ a.interview_datetime }}</td><td>{{ a.feedback }}</td>
          <td v-if="a.status === 'Offer'">
            <button class="btn btn-sm btn-success me-1" @click="acceptOffer(a.id)">Accept</button>
            <button class="btn btn-sm btn-danger" @click="declineOffer(a.id)">Decline</button>
          </td>
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
      studentProfileForm: { name: "", degree: "", branch: "", year: "", contact: "", cgpa: "", skills: "", experience: "" },
      selectedResume: null, exportMessage: "", currentExportJobId: null, exportReady: false,
      message: "", successMessage: "",
      openJobs: [], myApplications: [], jobSearch: "", eligibleOnly: false
    }
  },
  async created() {
    await this.loadStudentData()
  },
  methods: {
    async loadStudentData() {
      await this.searchJobs()
      this.myApplications = (await api.get("/student/applications")).data
      this.studentProfileForm = (await api.get("/student/profile")).data
    },
    async saveStudentProfile() {
      try {
        const res = await api.put("/student/profile", this.studentProfileForm)
        this.successMessage = res.data.message
        this.message = ""
        await this.loadStudentData()
      } catch (error) {
        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async uploadResume() {

      if (!this.selectedResume) {
        this.message = "Please select a PDF file"
        return
      }

      const formData = new FormData()
      formData.append("resume", this.selectedResume)

      try {

        const res = await api.post(
          "/student/resume/upload",
          formData
        )

        this.successMessage = res.data.message
        this.message = ""

        await this.loadStudentData()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }

    },
    async searchJobs() {
      this.openJobs = (await api.get("/student/jobs", { params: { q: this.jobSearch, eligible_only: this.eligibleOnly } })).data
    },
    async applyJob(jobId) {
      try {
        const res = await api.post(`/student/jobs/${jobId}/apply`)
        this.successMessage = res.data.message
        this.message = ""
        this.myApplications = (await api.get("/student/applications")).data
      } catch (error) {
        this.message = error.response?.data?.message
        this.successMessage = ""
      }
    },
    async acceptOffer(applicationId) {
      try {

        const res = await api.post(`/student/applications/${applicationId}/accept-offer`)

        this.successMessage = res.data.message
        this.message = ""

        this.myApplications = (await api.get("/student/applications")).data

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async declineOffer(applicationId) {
      try {

        const res = await api.post(`/student/applications/${applicationId}/decline-offer`)

        this.successMessage = res.data.message
        this.message = ""

        this.myApplications = (await api.get("/student/applications")).data

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    },
    async downloadOfferLetter() {
      try {
        const res = await api.get("/student/placement/offer-letter")
        const blob = new Blob([res.data], { type: "text/plain" })
        const link = document.createElement("a")
        link.href = URL.createObjectURL(blob)
        link.download = "offer_letter.txt"
        link.click()
      } catch (error) {
        this.exportMessage = "No placement record found yet"
      }
    },
    async exportCsv() {
      this.message = ""
      this.successMessage = ""
      this.exportReady = false
      const res = await api.post("/student/applications/export")
      this.exportMessage = "Export started in background..."
      this.currentExportJobId = res.data.export_job_id
      const jobId = this.currentExportJobId
      const interval = setInterval(async () => {
        const r = await api.get(`/student/applications/export/${jobId}/status`)
        if (r.data.status === "ready") {
          clearInterval(interval)
          this.exportMessage = "Your CSV export is ready!"
          this.exportReady = true
        }
      }, 2000)
    },
    async downloadExportCsv() {
      this.message = ""
      this.successMessage = ""
      const res = await api.get(`/student/applications/export/${this.currentExportJobId}/download`, { responseType: "blob" })
      const blob = new Blob([res.data], { type: "text/csv" })
      const link = document.createElement("a")
      link.href = URL.createObjectURL(blob)
      link.download = "my_applications.csv"
      link.click()
    }
  }
}
</script>
