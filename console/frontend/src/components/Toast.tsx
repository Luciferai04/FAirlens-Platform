import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";

interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  showToast: (message: string, type?: Toast["type"]) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

let toastId = 0;

export const ToastProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, type: Toast["type"] = "success") => {
      const id = ++toastId;
      setToasts((prev) => [...prev, { id, message, type }]);
    },
    []
  );

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

const BORDER_COLORS = {
  success: "border-[#10a37f]",
  error: "border-error",
  info: "border-primary-container",
};

const ICONS = {
  success: "check_circle",
  error: "error",
  info: "info",
};

const ICON_COLORS = {
  success: "text-[#10a37f]",
  error: "text-error",
  info: "text-primary-container",
};

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: (id: number) => void;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Animate in
    requestAnimationFrame(() => setVisible(true));
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(toast.id), 300);
    }, 3000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div
      className={`pointer-events-auto bg-[#171717] border ${
        BORDER_COLORS[toast.type]
      } text-white px-4 py-3 rounded-lg flex items-center gap-3 shadow-xl transition-all duration-300 ${
        visible
          ? "translate-y-0 opacity-100"
          : "translate-y-4 opacity-0"
      }`}
    >
      <span
        className={`material-symbols-outlined ${ICON_COLORS[toast.type]} text-[20px]`}
        style={{ fontVariationSettings: "'FILL' 1" }}
      >
        {ICONS[toast.type]}
      </span>
      <span className="text-body-md">{toast.message}</span>
      <button
        onClick={() => {
          setVisible(false);
          setTimeout(() => onDismiss(toast.id), 300);
        }}
        className="text-[#b4b4b4] hover:text-white ml-2 transition-colors"
      >
        <span className="material-symbols-outlined text-[16px]">close</span>
      </button>
    </div>
  );
}

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be inside ToastProvider");
  return ctx;
};
