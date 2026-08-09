import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { uploadResume } from "../services/resumeService";
import { listJobs } from "../services/jobService";

export default function ResumeUpload() {
  const navigate = useNavigate();

  const [jobs, setJobs] = useState([]);
  const [file, setFile] = useState(null);
  const [versionLabel, setVersionLabel] = useState("");
  const [jobId, setJobId] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listJobs({ limit: 100 })
      .then(setJobs)
      .catch(() => setJobs([]));
  }, []);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    setError("");
    if (selected && selected.type !== "application/pdf") {
      setError("Please choose a PDF file.");
      setFile(null);
      return;
    }
    setFile(selected || null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError("Please choose a PDF resume to upload.");
      return;
    }
    setError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const resume = await uploadResume({
        file,
        versionLabel: versionLabel || undefined,
        jobId: jobId || undefined,
      });

      if (jobId) {
        // Analysis was scheduled in the background — go watch it complete
        navigate(`/ai-result/${resume.id}`);
      } else {
        setSuccessMessage("Resume uploaded successfully.");
        setFile(null);
        setVersionLabel("");
        e.target.reset?.();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <MainLayout>
      <div className="mx-auto max-w-xl">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">Upload resume</h1>
          <p className="mt-1 text-sm text-slate-500">
            Add a new resume version, optionally matched against a job.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
                {successMessage}
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                PDF file <span className="font-normal text-slate-400">(max 5MB)</span>
              </label>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-4 py-8 text-center transition hover:border-brand-400 hover:bg-brand-50/40">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="mb-2 text-slate-400">
                  <path d="M12 16V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" strokeLinecap="round" />
                </svg>
                <span className="text-sm font-medium text-slate-700">
                  {file ? file.name : "Click to choose a PDF"}
                </span>
                <span className="mt-1 text-xs text-slate-400">or drag and drop</span>
                <input type="file" accept="application/pdf" onChange={handleFileChange} className="hidden" />
              </label>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Version label <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <input
                value={versionLabel}
                onChange={(e) => setVersionLabel(e.target.value)}
                placeholder="e.g. backend-focused"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Match against a job <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <select
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">Don't run AI analysis</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.company_name} — {job.job_title}
                  </option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-slate-400">
                Selecting a job runs AI match analysis in the background after upload.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-1 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Uploading…" : "Upload resume"}
            </button>
          </form>
        </div>
      </div>
    </MainLayout>
  );
}
