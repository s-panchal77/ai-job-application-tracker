import { useEffect, useState, useCallback, useRef } from "react";
import MainLayout from "../layouts/MainLayout";
import Loader from "../components/Loader";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";
import {
  listJobs,
  createJob,
  updateJob,
  deleteJob,
  JOB_STATUSES,
} from "../services/jobService";

// ── Constants ───────────────────────────────────────────────

const PAGE_SIZE = 10;

const STATUS_STYLES = {
  Applied: "bg-slate-100 text-slate-700",
  "OA Scheduled": "bg-amber-50 text-amber-700",
  Interview: "bg-brand-50 text-brand-700",
  Rejected: "bg-red-50 text-red-700",
  Selected: "bg-green-50 text-green-700",
};

const EMPTY_FORM = {
  company_name: "",
  job_title: "",
  location: "",
  status: "Applied",
  job_description: "",
  notes: "",
};

// ── Job Form Modal ───────────────────────────────────────────

function JobFormModal({ initialData, onClose, onSave }) {
  const [form, setForm] = useState(initialData || EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const isEditing = Boolean(initialData?.id);

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsSaving(true);
    try {
      await onSave(form, initialData?.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save this job. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            {isEditing ? "Edit job application" : "Add job application"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Company</label>
              <input
                required
                value={form.company_name}
                onChange={(e) => handleChange("company_name", e.target.value)}
                placeholder="Google"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Role</label>
              <input
                required
                value={form.job_title}
                onChange={(e) => handleChange("job_title", e.target.value)}
                placeholder="Backend Developer"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Location</label>
              <input
                value={form.location || ""}
                onChange={(e) => handleChange("location", e.target.value)}
                placeholder="Remote"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Status</label>
              <select
                value={form.status}
                onChange={(e) => handleChange("status", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                {JOB_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Job description{" "}
              <span className="font-normal text-slate-400">(used for AI matching)</span>
            </label>
            <textarea
              rows={4}
              value={form.job_description || ""}
              onChange={(e) => handleChange("job_description", e.target.value)}
              placeholder="Paste the job description here…"
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Notes</label>
            <textarea
              rows={2}
              value={form.notes || ""}
              onChange={(e) => handleChange("notes", e.target.value)}
              placeholder="Any personal notes about this application"
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div className="mt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? "Saving…" : isEditing ? "Save changes" : "Add job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Pagination Controls ──────────────────────────────────────

function Pagination({ page, hasMore, onPrev, onNext, totalOnPage }) {
  return (
    <div className="mt-4 flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-card">
      <span className="text-xs text-slate-400">
        Page {page} · {totalOnPage} result{totalOnPage !== 1 ? "s" : ""}
      </span>
      <div className="flex gap-2">
        <button
          onClick={onPrev}
          disabled={page === 1}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          ← Previous
        </button>
        <button
          onClick={onNext}
          disabled={!hasMore}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────

export default function Jobs() {
  const { toasts, showToast, removeToast } = useToast();

  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalJob, setModalJob] = useState(undefined); // undefined = closed, null = create, object = edit
  const [deletingId, setDeletingId] = useState(null);

  // Search & filter state
  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Pagination state
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // Debounce ref
  const debounceRef = useRef(null);

  // ── Data loading ──────────────────────────────────────────

  const loadJobs = useCallback(
    async (search, status, pageNum) => {
      setIsLoading(true);
      try {
        const skip = (pageNum - 1) * PAGE_SIZE;
        const params = { skip, limit: PAGE_SIZE };
        if (search) params.search = search;
        if (status) params.status = status;

        const data = await listJobs(params);
        setJobs(data);
        // If we got a full page, there might be more
        setHasMore(data.length === PAGE_SIZE);
      } catch (err) {
        console.error("Failed to load jobs", err);
        showToast("Failed to load jobs. Please try again.", "error");
      } finally {
        setIsLoading(false);
      }
    },
    [showToast]
  );

  // Load whenever search / filter / page changes
  useEffect(() => {
    loadJobs(activeSearch, statusFilter, page);
  }, [activeSearch, statusFilter, page, loadJobs]);

  // ── Search debounce ───────────────────────────────────────

  function handleSearchChange(e) {
    const value = e.target.value;
    setSearchInput(value);

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1); // reset to page 1 on new search
      setActiveSearch(value);
    }, 400);
  }

  function handleStatusChange(e) {
    setPage(1);
    setStatusFilter(e.target.value);
  }

  function handleClearFilters() {
    setSearchInput("");
    setActiveSearch("");
    setStatusFilter("");
    setPage(1);
  }

  // ── CRUD handlers ─────────────────────────────────────────

  async function handleSave(form, jobId) {
    if (jobId) {
      await updateJob(jobId, form);
      showToast("Job application updated.", "success");
    } else {
      await createJob(form);
      showToast("Job application added.", "success");
    }
    setModalJob(undefined);
    setPage(1);
    await loadJobs(activeSearch, statusFilter, 1);
  }

  async function handleDelete(jobId) {
    if (!window.confirm("Delete this job application? This can't be undone.")) return;
    setDeletingId(jobId);
    try {
      await deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      showToast("Job application deleted.", "success");
    } catch (err) {
      console.error("Failed to delete job", err);
      showToast("Failed to delete job application.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  // ── UI helpers ────────────────────────────────────────────

  const hasFilters = activeSearch || statusFilter;
  const isFiltered = hasFilters;

  return (
    <MainLayout>
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Job applications</h1>
            <p className="mt-1 text-sm text-slate-500">Track every company you've applied to.</p>
          </div>
          <button
            onClick={() => setModalJob(null)}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Add job
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* Search input */}
          <div className="relative flex-1">
            <svg
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" strokeLinecap="round" />
            </svg>
            <input
              id="job-search"
              type="search"
              value={searchInput}
              onChange={handleSearchChange}
              placeholder="Search company or role…"
              className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Status filter */}
          <select
            id="job-status-filter"
            value={statusFilter}
            onChange={handleStatusChange}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 sm:w-44"
          >
            <option value="">All statuses</option>
            {JOB_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          {/* Clear filters */}
          {isFiltered && (
            <button
              onClick={handleClearFilters}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-50"
            >
              Clear
            </button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <Loader size="lg" label="Loading jobs…" />
        ) : jobs.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <svg
              className="mx-auto mb-3 text-slate-300"
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <rect x="3" y="7" width="18" height="13" rx="2" />
              <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
            {isFiltered ? (
              <>
                <p className="text-sm font-medium text-slate-600">No results match your search</p>
                <p className="mt-1 text-sm text-slate-400">
                  Try adjusting your search term or status filter.
                </p>
                <button
                  onClick={handleClearFilters}
                  className="mt-4 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Clear filters
                </button>
              </>
            ) : (
              <>
                <p className="text-sm font-medium text-slate-600">No job applications yet</p>
                <p className="mt-1 text-sm text-slate-400">
                  Add your first one to start tracking your search.
                </p>
                <button
                  onClick={() => setModalJob(null)}
                  className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
                >
                  Add job
                </button>
              </>
            )}
          </div>
        ) : (
          <>
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
              {/* Table — larger screens */}
              <table className="hidden w-full text-left text-sm sm:table">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">Company</th>
                    <th className="px-5 py-3 font-medium">Role</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Applied</th>
                    <th className="px-5 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50/60">
                      <td className="px-5 py-3 font-medium text-slate-800">{job.company_name}</td>
                      <td className="px-5 py-3 text-slate-600">{job.job_title}</td>
                      <td className="px-5 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                            STATUS_STYLES[job.status] || "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-500">
                        {new Date(job.applied_date).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setModalJob(job)}
                            className="rounded-md px-2.5 py-1 text-xs font-medium text-brand-600 hover:bg-brand-50"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(job.id)}
                            disabled={deletingId === job.id}
                            className="rounded-md px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            {deletingId === job.id ? "Deleting…" : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Stacked cards — mobile */}
              <div className="divide-y divide-slate-100 sm:hidden">
                {jobs.map((job) => (
                  <div key={job.id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-slate-800">{job.company_name}</p>
                        <p className="text-sm text-slate-500">{job.job_title}</p>
                      </div>
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                          STATUS_STYLES[job.status] || "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <p className="text-xs text-slate-400">
                        Applied {new Date(job.applied_date).toLocaleDateString()}
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setModalJob(job)}
                          className="rounded-md px-2.5 py-1 text-xs font-medium text-brand-600 hover:bg-brand-50"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(job.id)}
                          className="rounded-md px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pagination */}
            <Pagination
              page={page}
              hasMore={hasMore}
              totalOnPage={jobs.length}
              onPrev={() => setPage((p) => Math.max(1, p - 1))}
              onNext={() => setPage((p) => p + 1)}
            />
          </>
        )}
      </div>

      {/* Job modal */}
      {modalJob !== undefined && (
        <JobFormModal
          initialData={modalJob}
          onClose={() => setModalJob(undefined)}
          onSave={handleSave}
        />
      )}

      {/* Toasts */}
      <Toast toasts={toasts} onDismiss={removeToast} />
    </MainLayout>
  );
}
