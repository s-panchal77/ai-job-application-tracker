import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import Loader from "../components/Loader";
import { getResumeAnalysis } from "../services/aiService";

const POLL_INTERVAL_MS = 3000;

function SkillPills({ skills, tone }) {
  const toneClasses =
    tone === "positive"
      ? "bg-green-50 text-green-700 border-green-200"
      : "bg-red-50 text-red-700 border-red-200";

  if (!skills || skills.length === 0) {
    return <p className="text-sm text-slate-400">None</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((skill) => (
        <span
          key={skill}
          className={`rounded-full border px-3 py-1 text-xs font-medium ${toneClasses}`}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function AIResult() {
  const { resumeId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const timerRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchStatus() {
      try {
        const data = await getResumeAnalysis(resumeId);
        if (!isMounted) return;
        setAnalysis(data);
        setError("");

        // Keep polling while the background task is still running.
        // Backend Phase 11: status is one of "pending" | "completed" | "failed".
        if (data.status === "pending") {
          timerRef.current = setTimeout(fetchStatus, POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (!isMounted) return;
        setError(err.response?.data?.detail || "Could not load analysis for this resume.");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    fetchStatus();

    return () => {
      isMounted = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [resumeId]);

  return (
    <MainLayout>
      <div className="mx-auto max-w-2xl">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-900">AI match analysis</h1>
          <p className="mt-1 text-sm text-slate-500">
            Results for resume #{resumeId}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
          {isLoading && !analysis && <Loader size="lg" label="Loading…" />}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {analysis?.status === "pending" && (
            <div className="flex flex-col items-center py-8 text-center">
              <Loader size="lg" />
              <p className="mt-2 text-sm font-medium text-slate-700">
                Analysis in progress…
              </p>
              <p className="mt-1 text-xs text-slate-400">
                This usually takes a few seconds. This page updates automatically.
              </p>
            </div>
          )}

          {analysis?.status === "failed" && (
            <div className="py-4">
              <div className="mb-4 flex items-center gap-2 text-red-700">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v5M12 16h.01" strokeLinecap="round" />
                </svg>
                <p className="text-sm font-semibold">Analysis failed</p>
              </div>
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {analysis.error_message || "Something went wrong while analyzing this resume."}
              </p>
            </div>
          )}

          {analysis?.status === "completed" && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xl font-bold text-brand-700">
                  {analysis.match_score}
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Match score</p>
                  <p className="text-lg font-semibold text-slate-900">
                    {analysis.match_score}/100
                  </p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-sm font-semibold text-slate-800">Matched skills</p>
                <SkillPills skills={analysis.matched_skills} tone="positive" />
              </div>

              <div>
                <p className="mb-2 text-sm font-semibold text-slate-800">Missing skills</p>
                <SkillPills skills={analysis.missing_skills} tone="negative" />
              </div>

              {analysis.suggestions?.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-semibold text-slate-800">Suggestions</p>
                  <ul className="flex flex-col gap-2">
                    {analysis.suggestions.map((s, i) => (
                      <li
                        key={i}
                        className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600"
                      >
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <Link
          to="/resume-upload"
          className="mt-4 inline-block text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          ← Upload another resume
        </Link>
      </div>
    </MainLayout>
  );
}
