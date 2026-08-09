import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Loader from "../components/Loader";
import { useAuth } from "../context/AuthContext";
import { getJobStats } from "../services/jobService";
import { listResumes } from "../services/resumeService";

// ── Stat Cards ──────────────────────────────────────────────

const STATUS_CARD_CONFIG = [
  {
    key: "applied",
    label: "Applied",
    accent: "bg-slate-100 text-slate-700 border-slate-200",
    dot: "bg-slate-400",
  },
  {
    key: "oa_scheduled",
    label: "OA Scheduled",
    accent: "bg-amber-50 text-amber-700 border-amber-200",
    dot: "bg-amber-400",
  },
  {
    key: "interview",
    label: "Interview",
    accent: "bg-brand-50 text-brand-700 border-brand-200",
    dot: "bg-brand-500",
  },
  {
    key: "rejected",
    label: "Rejected",
    accent: "bg-red-50 text-red-700 border-red-200",
    dot: "bg-red-400",
  },
  {
    key: "selected",
    label: "Selected",
    accent: "bg-green-50 text-green-700 border-green-200",
    dot: "bg-green-400",
  },
];

function StatusCard({ label, value, accent, dot }) {
  return (
    <div className={`rounded-2xl border p-5 shadow-card ${accent}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}

function SummaryCard({ label, value, hint }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

function QuickAction({ to, title, description, icon }) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-brand-200 hover:shadow-md"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 transition group-hover:bg-brand-600 group-hover:text-white">
        {icon}
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-800">{title}</p>
        <p className="mt-0.5 text-sm text-slate-500">{description}</p>
      </div>
    </Link>
  );
}

// ── Page ────────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, resumesData] = await Promise.all([
          getJobStats(),
          listResumes(),
        ]);
        setStats(statsData);
        setResumes(resumesData.resumes || []);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const latestResume = resumes[0]; // backend returns newest first

  return (
    <MainLayout>
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">
            Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Here's an overview of your job search progress.
          </p>
        </div>

        {isLoading ? (
          <Loader size="lg" label="Loading your dashboard…" />
        ) : (
          <>
            {/* ── Application Status Breakdown ── */}
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Application Status
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 mb-6">
              {STATUS_CARD_CONFIG.map(({ key, label, accent, dot }) => (
                <StatusCard
                  key={key}
                  label={label}
                  value={stats?.[key] ?? 0}
                  accent={accent}
                  dot={dot}
                />
              ))}
            </div>

            {/* ── Overview Summary ── */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-8">
              <SummaryCard
                label="Total Applications"
                value={stats?.total ?? 0}
                hint="All applications tracked"
              />
              <SummaryCard label="Total Resumes" value={resumes.length} hint="Versions uploaded" />
              <SummaryCard
                label="Latest Resume"
                value={latestResume ? latestResume.version_label || "Untitled" : "—"}
                hint={
                  latestResume
                    ? new Date(latestResume.uploaded_at).toLocaleDateString()
                    : "No resumes uploaded yet"
                }
              />
            </div>

            {/* ── Quick Actions ── */}
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Quick actions
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <QuickAction
                to="/jobs"
                title="Add a job application"
                description="Track a new company and role"
                icon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 5v14M5 12h14" strokeLinecap="round" />
                  </svg>
                }
              />
              <QuickAction
                to="/resume-upload"
                title="Upload a resume"
                description="Get an AI match score against a job"
                icon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 16V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" strokeLinecap="round" />
                  </svg>
                }
              />
              <QuickAction
                to="/resumes"
                title="Manage resumes"
                description="View, download, or set your active version"
                icon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                }
              />
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}
