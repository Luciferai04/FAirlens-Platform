import React, { ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { Link } from 'react-router-dom';

type Role = 'viewer' | 'auditor' | 'admin' | 'owner';

interface RequireRoleProps {
  role: Role;
  children: ReactNode;
  fallback?: ReactNode;
}

export const RequireRole: React.FC<RequireRoleProps> = ({ role, children, fallback }) => {
  const { hasRole, loading } = useAuth();

  if (loading) return null;

  if (!hasRole(role)) {
    if (fallback) return <>{fallback}</>;
    
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-background p-lg">
        <div className="w-24 h-24 bg-error-container/10 rounded-full flex items-center justify-center mb-6 border-2 border-error-container/20">
          <span className="material-symbols-outlined text-error text-[48px]">shield</span>
        </div>
        <h2 className="font-h2 text-h2 text-on-surface mb-2">Access Denied</h2>
        <p className="text-body-md text-on-surface-variant mb-8 text-center max-w-md">
          Your current role does not have permission to view this resource. 
          Please contact your administrator for elevated access.
        </p>
        <Link to="/" className="flex items-center gap-2 text-primary hover:underline">
          <span className="material-symbols-outlined text-[16px]">arrow_back</span> Return to Dashboard
        </Link>
      </div>
    );
  }

  return <>{children}</>;
};
