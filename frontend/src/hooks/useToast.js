import { useState, useCallback } from "react";

let _id = 0;

/**
 * useToast — manages a queue of toast notifications.
 *
 * Returns:
 *   toasts      — current array of { id, message, type }
 *   showToast   — showToast(message, type = "success" | "error" | "info")
 *   removeToast — removeToast(id)
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message, type = "success") => {
      const id = ++_id;
      setToasts((prev) => [...prev, { id, message, type }]);

      // Auto-dismiss after 3.5 s
      setTimeout(() => removeToast(id), 3500);
    },
    [removeToast]
  );

  return { toasts, showToast, removeToast };
}
