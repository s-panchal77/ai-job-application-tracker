// A small, reusable spinner. size: "sm" | "md" | "lg"
export default function Loader({ size = "md", label }) {
  const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-6 w-6 border-2",
    lg: "h-10 w-10 border-[3px]",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3 py-6">
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-slate-200 border-t-brand-600`}
        role="status"
        aria-label="Loading"
      />
      {label && <p className="text-sm text-slate-500">{label}</p>}
    </div>
  );
}
