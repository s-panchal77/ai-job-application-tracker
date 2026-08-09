import api from "../api/axios";

// GET /resumes/{id}/analysis — returns pending/completed/failed shape
// exactly as defined by the backend's AnalysisStatusResponse (Phase 11).
export async function getResumeAnalysis(resumeId) {
  const response = await api.get(`/resumes/${resumeId}/analysis`);
  return response.data;
}
