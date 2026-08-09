import api from "../api/axios";

// POST /resumes/upload — multipart/form-data.
// Backend accepts: file (required), version_label (optional),
// job_id (optional — triggers background AI analysis, Phase 11).
export async function uploadResume({ file, versionLabel, jobId }) {
  const formData = new FormData();
  formData.append("file", file);
  if (versionLabel) formData.append("version_label", versionLabel);
  if (jobId) formData.append("job_id", jobId);

  const response = await api.post("/resumes/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// GET /resumes/ — returns { total, resumes: [...] }
export async function listResumes() {
  const response = await api.get("/resumes/");
  return response.data;
}

// PATCH /resumes/{id}/set-active — marks one resume as the active version.
export async function setActiveResume(resumeId) {
  const response = await api.patch(`/resumes/${resumeId}/set-active`);
  return response.data;
}

// GET /resumes/{id}/download — Axios blob download.
// The Authorization header is attached automatically by the request interceptor
// in api/axios.js. The JWT is NEVER placed in a URL query parameter.
export async function downloadResume(resumeId, filename) {
  const response = await api.get(`/resumes/${resumeId}/download`, {
    responseType: "blob",
  });

  // Create a temporary object URL and click it to trigger the browser save dialog.
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename || `resume_${resumeId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export async function deleteResume(resumeId) {
  await api.delete(`/resumes/${resumeId}`);
}
