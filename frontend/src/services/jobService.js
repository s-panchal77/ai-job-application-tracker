import api from "../api/axios";

// GET /jobs/ — supports optional filtering/search/pagination,
// matching the backend's query parameters exactly (Phase 7).
export async function listJobs(params = {}) {
  const response = await api.get("/jobs/", { params });
  return response.data;
}

export async function getJob(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

export async function createJob(jobData) {
  const response = await api.post("/jobs/", jobData);
  return response.data;
}

export async function updateJob(jobId, jobData) {
  const response = await api.patch(`/jobs/${jobId}`, jobData);
  return response.data;
}

export async function deleteJob(jobId) {
  await api.delete(`/jobs/${jobId}`);
}

// GET /jobs/stats — returns per-status counts for the current user.
export async function getJobStats() {
  const response = await api.get("/jobs/stats");
  return response.data;
}

// Fixed set of statuses — mirrors the backend's ApplicationStatus enum
// (models/job.py) so the frontend never invents a value the API would reject.
export const JOB_STATUSES = [
  "Applied",
  "OA Scheduled",
  "Interview",
  "Rejected",
  "Selected",
];
