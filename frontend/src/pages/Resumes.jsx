import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Loader from "../components/Loader";
import Toast from "../components/Toast";
import { useToast } from "../hooks/useToast";
import {
  listResumes,
  downloadResume,
  deleteResume,
  setActiveResume,
} from "../services/resumeService";

// ── Helpers ──────────────────────────────────────────────────

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
} 

// ── Active Badge ─────────────────────────────────────────────

function ActiveBadge({ isActive }) {
  if (isActive) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
        Active
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
      Inactive
    </span>
  );
}

// ── Resume Card (mobile) ─────────────────────────────────────

function ResumeCard({ resume, onDownload, onSetActive, onDelete, isSettingActive, isDeleting }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      {/* File name + active badge */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-800">
              {resume.original_filename}
            </p>
            <p className="text-xs text-slate-400">
              {resume.version_label ? `v: ${resume.version_label}` : "No version label"}
            </p>
          </div>
        </div>
        <ActiveBadge isActive={resume.is_active} />
      </div>

      {/* Meta */}
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
        <span>{formatFileSize(resume.file_size)}</span>
        <span>Uploaded {formatDate(resume.uploaded_at)}</span>
      </div>

      {/* Actions */}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          onClick={() => onDownload(resume)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 16V4M12 16l-4-4M12 16l4-4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 20h16" strokeLinecap="round" />
          </svg>
          Download
        </button>

        {!resume.is_active && (
          <button
            onClick={() => onSetActive(resume.id)}
            disabled={isSettingActive === resume.id}
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-100 disabled:opacity-60"
          >
            {isSettingActive === resume.id ? "Setting…" : "Set Active"}
          </button>
        )}

        <button
          onClick={() => onDelete(resume)}
          disabled={isDeleting === resume.id}
          className="inline-flex items-center gap-1.5 rounded-lg border border-red-100 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-100 disabled:opacity-50"
        >
          {isDeleting === resume.id ? "Deleting…" : "Delete"}
        </button>
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────

export default function Resumes() {
  const { toasts, showToast, removeToast } = useToast();

  const [resumes, setResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSettingActive, setIsSettingActive] = useState(null);
  const [isDeleting, setIsDeleting] = useState(null);
  const [isDownloading, setIsDownloading] = useState(null);

  async function loadResumes() {
    setIsLoading(true);
    try {
      const data = await listResumes();
      setResumes(data.resumes || []);
    } catch (err) {
      console.error("Failed to load resumes", err);
      showToast("Failed to load resumes. Please try again.", "error");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadResumes();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Download ─────────────────────────────────────────────

  async function handleDownload(resume) {
    setIsDownloading(resume.id);
    try {
      await downloadResume(resume.id, resume.original_filename);
      showToast(`Downloading "${resume.original_filename}"…`, "info");
    } catch (err) {
      console.error("Download failed", err);
      showToast("Download failed. Please try again.", "error");
    } finally {
      setIsDownloading(null);
    }
  }

  // ── Set Active ───────────────────────────────────────────

  async function handleSetActive(resumeId) {
    setIsSettingActive(resumeId);
    try {
      await setActiveResume(resumeId);
      // Optimistically update the list
      setResumes((prev) =>
        prev.map((r) => ({ ...r, is_active: r.id === resumeId }))
      );
      showToast("Active resume updated.", "success");
    } catch (err) {
      console.error("Set active failed", err);
      showToast("Could not update active resume. Please try again.", "error");
    } finally {
      setIsSettingActive(null);
    }
  }

  // ── Delete ───────────────────────────────────────────────

  async function handleDelete(resume) {
    if (
      !window.confirm(
        `Delete "${resume.original_filename}"? This cannot be undone and will remove the file from disk.`
      )
    )
      return;

    setIsDeleting(resume.id);
    try {
      await deleteResume(resume.id);
      setResumes((prev) => prev.filter((r) => r.id !== resume.id));
      showToast(`"${resume.original_filename}" deleted.`, "success");
    } catch (err) {
      console.error("Delete failed", err);
      showToast("Could not delete resume. Please try again.", "error");
    } finally {
      setIsDeleting(null);
    }
  }

  // ── Render ───────────────────────────────────────────────

  return (
    <MainLayout>
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">My Resumes</h1>
            <p className="mt-1 text-sm text-slate-500">
              Manage all uploaded resume versions.
            </p>
          </div>
          <Link
            to="/resume-upload"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            Upload new
          </Link>
        </div>

        {/* Content */}
        {isLoading ? (
          <Loader size="lg" label="Loading resumes…" />
        ) : resumes.length === 0 ? (
          /* Empty state */
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-14 text-center">
            <svg
              className="mx-auto mb-3 text-slate-300"
              width="44"
              height="44"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.25"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="12" x2="12" y2="18" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
            <p className="text-sm font-medium text-slate-600">No resumes uploaded yet</p>
            <p className="mt-1 text-sm text-slate-400">
              Upload your first resume to get started.
            </p>
            <Link
              to="/resume-upload"
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Upload resume
            </Link>
          </div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card sm:block">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">File</th>
                    <th className="px-5 py-3 font-medium">Version</th>
                    <th className="px-5 py-3 font-medium">Size</th>
                    <th className="px-5 py-3 font-medium">Uploaded</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {resumes.map((resume) => (
                    <tr key={resume.id} className="hover:bg-slate-50/60">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                            </svg>
                          </div>
                          <span className="max-w-[200px] truncate font-medium text-slate-800">
                            {resume.original_filename}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-slate-500">
                        {resume.version_label || (
                          <span className="italic text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-slate-500">
                        {formatFileSize(resume.file_size)}
                      </td>
                      <td className="px-5 py-3 text-slate-500">
                        {formatDate(resume.uploaded_at)}
                      </td>
                      <td className="px-5 py-3">
                        <ActiveBadge isActive={resume.is_active} />
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center justify-end gap-2">
                          {/* Download */}
                          <button
                            onClick={() => handleDownload(resume)}
                            disabled={isDownloading === resume.id}
                            title="Download PDF"
                            className="rounded-md px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                          >
                            {isDownloading === resume.id ? "…" : "Download"}
                          </button>

                          {/* Set active — only shown when not already active */}
                          {!resume.is_active && (
                            <button
                              onClick={() => handleSetActive(resume.id)}
                              disabled={isSettingActive === resume.id}
                              className="rounded-md px-2.5 py-1 text-xs font-medium text-brand-600 hover:bg-brand-50 disabled:opacity-50"
                            >
                              {isSettingActive === resume.id ? "Setting…" : "Set Active"}
                            </button>
                          )}

                          {/* Delete */}
                          <button
                            onClick={() => handleDelete(resume)}
                            disabled={isDeleting === resume.id}
                            className="rounded-md px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            {isDeleting === resume.id ? "Deleting…" : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="flex flex-col gap-4 sm:hidden">
              {resumes.map((resume) => (
                <ResumeCard
                  key={resume.id}
                  resume={resume}
                  onDownload={handleDownload}
                  onSetActive={handleSetActive}
                  onDelete={handleDelete}
                  isSettingActive={isSettingActive}
                  isDeleting={isDeleting}
                />
              ))}
            </div>

            {/* Summary footer */}
            <p className="mt-4 text-xs text-slate-400">
              {resumes.length} resume{resumes.length !== 1 ? "s" : ""} · Only one can be active at a time.
            </p>
          </>
        )}
      </div>

      <Toast toasts={toasts} onDismiss={removeToast} />
    </MainLayout>
  );
}
