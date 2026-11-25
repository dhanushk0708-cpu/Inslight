import React from "react";

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => (
  <div className="empty-state-card">
    <div className="empty-state-icon">{icon}</div>
    <h4 className="empty-state-title">{title}</h4>
    <p className="empty-state-desc">{description}</p>
    {actionLabel && onAction && (
      <button type="button" className="btn btn-primary" onClick={onAction} style={{ marginTop: 14 }}>
        {actionLabel}
      </button>
    )}
  </div>
);
