import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

type Role = 'viewer' | 'auditor' | 'admin' | 'owner';

export interface User {
  uid: string;
  email: string;
  displayName: string;
  photoURL: string | null;
}

interface AuthContextType {
  user: User | null;
  role: Role | null;
  loading: boolean;
  isDemoMode: boolean;
  loginWithCredential: (userInfo: any, token: string) => void;
  loginDemo: () => void;
  logout: () => void;
  hasRole: (requiredRole: Role) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ROLE_HIERARCHY: Role[] = ['viewer', 'auditor', 'admin', 'owner'];

// Check demo mode from both build-time env AND localStorage
const checkDemoMode = () =>
  import.meta.env.VITE_DEMO_MODE === 'true' ||
  (typeof window !== 'undefined' && localStorage.getItem('demo_mode') === 'true');

const DEMO_USER: User = {
  uid: 'demo-user',
  email: 'demo@fairlens.ai',
  displayName: 'Demo Admin',
  photoURL: null,
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(checkDemoMode);
  const [user, setUser] = useState<User | null>(isDemoMode ? DEMO_USER : null);
  const [role, setRole] = useState<Role | null>(isDemoMode ? 'admin' : null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If demo mode is active, set demo state immediately
    if (isDemoMode) {
      setUser(DEMO_USER);
      setRole('admin');
      setLoading(false);
      return;
    }

    // Otherwise, try to load session from localStorage
    const savedUser = localStorage.getItem('google_user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
        setRole('admin'); // Set default role
      } catch (err) {
        localStorage.removeItem('google_user');
      }
    }
    setLoading(false);
  }, [isDemoMode]);

  const loginWithCredential = useCallback((userInfo: any, token: string) => {
    // Domain Restriction Check
    const allowedDomain = import.meta.env.VITE_ALLOWED_DOMAIN;
    if (allowedDomain && userInfo.email && !userInfo.email.endsWith(`@${allowedDomain}`)) {
      throw new Error(`Access restricted to @${allowedDomain} accounts only.`);
    }

    const newUser = {
      uid: userInfo.sub || userInfo.id || 'google-user',
      email: userInfo.email,
      displayName: userInfo.name,
      photoURL: userInfo.picture || null,
    };

    // Save token and set state
    localStorage.setItem('google_user', JSON.stringify(newUser));
    localStorage.setItem('google_jwt', token);
    setUser(newUser);
    setRole('admin');
    setIsDemoMode(false);
  }, []);

  const loginDemo = useCallback(() => {
    localStorage.setItem('demo_mode', 'true');
    setIsDemoMode(true);
    setUser(DEMO_USER);
    setRole('admin');
  }, []);

  const logout = useCallback(() => {
    // Clear demo mode
    localStorage.removeItem('demo_mode');
    setIsDemoMode(false);

    // Clear Google user
    localStorage.removeItem('google_user');
    localStorage.removeItem('google_jwt');
    setUser(null);
    setRole(null);
  }, []);

  const hasRole = useCallback((requiredRole: Role) => {
    if (!role) return false;
    const currentIdx = ROLE_HIERARCHY.indexOf(role);
    const requiredIdx = ROLE_HIERARCHY.indexOf(requiredRole);
    return currentIdx >= requiredIdx;
  }, [role]);

  return (
    <AuthContext.Provider value={{ user, role, loading, isDemoMode, loginWithCredential, loginDemo, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
