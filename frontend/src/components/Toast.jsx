/**
 * Toast — renders a fixed-position stack of dismissible notifications.
 *
 * Props:
 *   toasts      — array of { id, message, type }
 *   onDismiss   — called with id when the close button is clicked
 *
 * Types: "success" | "error" | "info"
 */

const TYPE_STYLES = {
  success: {
    container: "border-green-200 bg-green-50 text-green-800",
    icon: "text-green-500",
    bar: "bg-green-400",
  },
  error: {
    container: "border-red-200 bg-red-50 text-red-800",
    icon: "text-red-500",
    bar: "bg-red-400",
  },
  info: {
    container: "border-brand-200 bg-brand-50 text-brand-800",
    icon: "text-brand-500",
    bar: "bg-brand-500",
  },
};

function ToastIcon({ type }) {
  if (type === "success") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (type === "error") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
    </svg>
  );
}

function ToastItem({ toast, onDismiss }) {
  const styles = TYPE_STYLES[toast.type] || TYPE_STYLES.info;

  return (
    <div
      className={`relative flex w-full max-w-sm items-start gap-3 overflow-hidden rounded-xl border px-4 py-3 shadow-lg ${styles.container}`}
      role="alert"
    >
      {/* Coloured accent bar on the left */}
      <div className={`absolute inset-y-0 left-0 w-1 ${styles.bar}`} />

      <span className={`mt-0.5 shrink-0 ${styles.icon}`}>
        <ToastIcon type={toast.type} />
      </span>

      <p className="flex-1 text-sm font-medium leading-snug">{toast.message}</p>

      <button
        onClick={() => onDismiss(toast.id)}
        className="ml-1 shrink-0 rounded p-0.5 opacity-60 hover:opacity-100"
        aria-label="Dismiss notification"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

export default function Toast({ toasts, onDismiss }) {
  if (!toasts.length) return null;

  return (
    <div
      className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
