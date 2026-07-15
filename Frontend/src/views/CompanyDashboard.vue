<template>
  <div class="container mt-4">
    <h3>Company Dashboard</h3>

    <button class="btn btn-secondary btn-sm mb-2" @click="exportCompanyCsv">Export Application/Placement History as CSV</button>
    <button v-if="companyExportReady" class="btn btn-success btn-sm mb-2 ms-2" @click="downloadCompanyExportCsv">Download CSV</button>
    <p class="text-success">{{ companyExportMessage }}</p>

    <div class="row mb-3">
      <div class="col"><div class="card p-2 text-center">Job Postings<br><b>{{ companySummary.total_job_postings }}</b></div></div>
      <div class="col"><div class="card p-2 text-center">Applications Received<br><b>{{ companySummary.total_applications_received }}</b></div></div>
      <div class="col"><div class="card p-2 text-center">Shortlisted<br><b>{{ (companySummary.shortlisted_candidates || []).length }}</b></div></div>
    </div>

    <div v-if="(companySummary.shortlisted_candidates || []).length > 0" class="mb-4">
      <h6>Shortlisted Candidates</h6>
      <table class="table table-bordered table-sm">
        <thead><tr><th>Student</th><th>Job</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="sc in companySummary.shortlisted_candidates" :key="sc.student_name + sc.job_title">
            <td>{{ sc.student_name }}</td><td>{{ sc.job_title }}</td><td>{{ sc.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h5>Company Profile</h5>
    <input v-model="profileForm.name" class="form-control mb-2" placeholder="Company Name">
    <input v-model="profileForm.industry" class="form-control mb-2" placeholder="Industry">
    <input v-model="profileForm.location" class="form-control mb-2" placeholder="Location">
    <input v-model="profileForm.hr_contact" class="form-control mb-2" placeholder="HR Contact">
    <input v-model="profileForm.website" class="form-control mb-2" placeholder="Website">
    <textarea v-model="profileForm.about" class="form-control mb-2" placeholder="About Company"></textarea>
    <button class="btn btn-outline-primary mb-4" @click="saveProfile">Save Profile</button>

    <h5>Post a New Job</h5>
    <input v-model="jobForm.title" class="form-control mb-2" placeholder="Job Title">
    <input v-model="jobForm.description" class="form-control mb-2" placeholder="Description">
    <input v-model="jobForm.salary" class="form-control mb-2" placeholder="Salary">
    <input v-model="jobForm.location" class="form-control mb-2" placeholder="Location">
    <input v-model="jobForm.skills_required" class="form-control mb-2" placeholder="Skills Required">
    <input v-model="jobForm.experience_required" class="form-control mb-2" placeholder="Experience Required">
    <input v-model="jobForm.eligible_branch" class="form-control mb-2" placeholder="Eligible Branch(es), comma separated">
    <input v-model="jobForm.min_cgpa" class="form-control mb-2" placeholder="Minimum CGPA">
    <input v-model="jobForm.eligible_year" class="form-control mb-2" placeholder="Eligible Year">
    <label class="form-label">Application Deadline</label>
    <input type="datetime-local" v-model="jobForm.application_deadline" class="form-control mb-2">
    <button class="btn btn-primary mb-2" @click="postJob">Post Job</button>
    <p class="text-success">{{ successMessage }}</p>
    <p class="text-danger">{{ message }}</p>

    <h5 class="mt-4">My Jobs</h5>
    <table class="table table-bordered table-sm">
      <thead><tr><th>Title</th><th>Approved</th><th>Status</th><th>Applications</th><th>Action</th></tr></thead>
      <tbody>
        <tr v-for="j in myJobs" :key="j.id">
          <td>{{ j.title }}</td><td>{{ j.is_approved }}</td><td>{{ j.status }}</td><td>{{ j.application_count }}</td>
          <td>
            <button v-if="j.status === 'Active'" class="btn btn-sm btn-warning me-1" @click="toggleJobStatus(j.id, 'Closed')">Close</button>
            <button v-else class="btn btn-sm btn-warning me-1" @click="toggleJobStatus(j.id, 'Active')">Reopen</button>
            <button class="btn btn-sm btn-primary" @click="viewApplicants(j.id)">View Applicants</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="selectedJobApplicants.length > 0 || viewingApplicants">
      <h5 class="mt-4">Applicants</h5>
      <table class="table table-bordered table-sm">
        <thead><tr><th>Student</th><th>Degree</th><th>Branch</th><th>Contact</th><th>Skills</th><th>Experience</th><th>Resume</th><th>CGPA</th><th>Status</th><th>Feedback</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="a in selectedJobApplicants" :key="a.application_id">
            <td>{{ a.student_name }}</td><td>{{ a.degree }}</td><td>{{ a.branch }}</td><td>{{ a.contact }}</td>
            <td>{{ a.skills }}</td><td>{{ a.experience }}</td><td><a v-if="a.resume_link" :href="a.resume_link" target="_blank" class="btn btn-sm btn-outline-primary">View Resume</a><span v-else>No Resume</span></td><td>{{ a.cgpa }}</td><td>{{ a.status }}</td><td>{{ a.feedback }}</td>
            <td>
              <div class="d-flex flex-column" style="gap: 4px; min-width: 220px;">
                <input v-model="feedbackText[a.application_id]" class="form-control form-control-sm" placeholder="Feedback (optional)">
                <input v-if="a.status !== 'Interview'" type="datetime-local" v-model="interviewTime[a.application_id]" class="form-control form-control-sm" title="Interview time">
                <input type="date" v-model="joiningDate[a.application_id]" class="form-control form-control-sm" title="Joining date (for Offer)">
                <div>
                  <button class="btn btn-sm btn-info me-1" @click="setStatus(a.application_id, 'Shortlisted')">Shortlist</button>
                  <button class="btn btn-sm btn-primary me-1" @click="setStatus(a.application_id, 'Interview')">Schedule Interview</button>
                  <button class="btn btn-sm btn-success me-1" @click="setStatus(a.application_id, 'Offer')">Send Offer</button>
                  <button class="btn btn-sm btn-danger" @click="setStatus(a.application_id, 'Rejected')">Reject</button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import api from "../api"

export default {
  data() {
    return {
      profileForm: { name: "", industry: "", location: "", about: "", hr_contact: "", website: "" },
      jobForm: { title: "", description: "", salary: "", location: "", skills_required: "",
        experience_required: "", eligible_branch: "", min_cgpa: "", eligible_year: "", application_deadline: "" },
      myJobs: [], companySummary: {}, companyExportMessage: "", currentCompanyExportJobId: null, companyExportReady: false,
      selectedJobApplicants: [], viewingApplicants: false, feedbackText: {}, interviewTime: {}, joiningDate: {},
      message: "", successMessage: ""
    }
  },
  async created() {
    await this.loadCompanyData()
  },
  methods: {
    async loadCompanyData() {
      this.myJobs = (await api.get("/company/jobs")).data
      this.companySummary = (await api.get("/company/dashboard-summary")).data
      const profileRes = await api.get("/company/profile")
      this.profileForm.name = profileRes.data.name
      this.profileForm.industry = profileRes.data.industry
      this.profileForm.location = profileRes.data.location
      this.profileForm.hr_contact = profileRes.data.hr_contact
      this.profileForm.website = profileRes.data.website
      this.profileForm.about = profileRes.data.about
    },
    async saveProfile() {
      try {
        const res = await api.put("/company/profile", this.profileForm)

        this.successMessage = res.data.message
        this.message = ""

        await this.loadCompanyData()

      } catch (error) {

        this.message = error.response?.data?.message
        this.successMessage = ""

      }
    
    },
    async postJob() {
      try {
        const res = await api.post("/company/jobs", this.jobForm)
        this.successMessage = res.data.message
        this.message = ""
        await this.loadCompanyData()
      } catch (error) {
        this.message = error.response?.data?.message
        this.successMessage = ""
      }
    },
    async toggleJobStatus(jobId, status) {
      try{
        const res = await api.put(`/company/jobs/${jobId}/status`, { status })
        this.successMessage = res.data.message
        this.message = ""
        await this.loadCompanyData()
      }
      catch(error){

        this.message = error.response?.data?.message
        this.successMessage = ""
      }
    },
    async viewApplicants(jobId) {
      this.viewingApplicants = true
      this.selectedJobApplicants = (await api.get(`/company/jobs/${jobId}/applications`)).data
    },
    async setStatus(applicationId, status) {
      const payload = { status, feedback: this.feedbackText[applicationId] || "" }
      if (status === "Interview") payload.interview_datetime = this.interviewTime[applicationId]
      if (status === "Offer") payload.joining_date = this.joiningDate[applicationId]
      try {
        const res =await api.put(`/company/applications/${applicationId}/status`, payload)
        this.successMessage = res.data.message
        this.message = ""
        await this.loadCompanyData()
      } catch (error) {
        this.message = error.response?.data?.message
        this.successMessage = ""
      }
    },
    async exportCompanyCsv() {
      this.companyExportReady = false
      const res = await api.post("/company/applications/export")
      this.companyExportMessage = "Export started in background..."
      this.currentCompanyExportJobId = res.data.export_job_id
      const interval = setInterval(async () => {
        const r = await api.get(`/company/applications/export/${this.currentCompanyExportJobId}/status`)
        if (r.data.status === "ready") {
          clearInterval(interval)
          this.companyExportMessage = "Your CSV export is ready!"
          this.companyExportReady = true
        }
      }, 2000)
    },
    async downloadCompanyExportCsv() {
      const res = await api.get(`/company/applications/export/${this.currentCompanyExportJobId}/download`, { responseType: "blob" })
      const blob = new Blob([res.data], { type: "text/csv" })
      const link = document.createElement("a")
      link.href = URL.createObjectURL(blob)
      link.download = "company_history.csv"
      link.click()
    }
  }
}
</script>
