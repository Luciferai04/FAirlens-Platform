import React from "react";

export const SkeletonRow = ({ cols = 6 }: { cols?: number }) => (
  <tr>
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="px-5 py-4">
        <div className="h-4 bg-surface-container-high rounded animate-pulse w-full" />
      </td>
    ))}
  </tr>
);

export const SkeletonCard = () => (
  <div className="bg-surface border border-outline-variant p-md rounded-xl h-32 animate-pulse">
    <div className="h-4 bg-surface-container-high rounded w-1/2 mb-4" />
    <div className="h-8 bg-surface-container-high rounded w-1/3" />
  </div>
);

export const SkeletonBar = () => (
  <div className="flex items-center gap-4 py-2">
    <div className="h-4 bg-surface-container-high rounded animate-pulse w-32" />
    <div className="flex-1 h-6 bg-surface-container rounded-full overflow-hidden">
      <div
        className="h-full bg-surface-container-high rounded-full animate-pulse"
        style={{ width: `${30 + Math.random() * 60}%` }}
      />
    </div>
  </div>
);

export const ErrorBanner = ({
  message = "Could not connect to the FairLens API. Check that the backend is running.",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) => (
  <div className="bg-error-container text-on-error-container p-4 rounded-lg flex items-center gap-3">
    <span className="material-symbols-outlined">wifi_off</span>
    <span className="text-body-md">{message}</span>
    {onRetry && (
      <button
        onClick={onRetry}
        className="ml-auto underline text-body-md hover:text-white transition-colors"
      >
        Retry
      </button>
    )}
  </div>
);
