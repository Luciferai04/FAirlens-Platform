import React, { useState, useRef, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/registry', label: 'Model Registry', icon: 'inventory_2' },
  { path: '/incidents', label: 'Incidents', icon: 'report_problem' },
  { path: '/compliance', label: 'Compliance', icon: 'verified_user' },
  { path: '/benchmarks', label: 'Benchmarks', icon: 'analytics' },
];

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const { user, logout, isDemoMode } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const displayName = user?.displayName || user?.email || 'User';
  const displayEmail = user?.email || 'demo@fairlens.ai';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const handleLogout = async () => {
    setShowDropdown(false);
    await logout();
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-surface font-body-md antialiased">
      {/* SideNavBar — matches Stitch v2 exactly */}
      <nav className="fixed left-0 top-0 h-full w-[240px] border-r border-[#2f2f2f] bg-[#171717] flex flex-col py-6 space-y-2 z-40 text-sm font-medium font-['Inter']">
        {/* Brand */}
        <div className="px-6 mb-lg flex items-center gap-sm">
          <div className="w-8 h-8 bg-primary-container rounded flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary-container text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              policy
            </span>
          </div>
          <div>
            <h1 className="text-white font-semibold">Governance Console</h1>
            <p className="text-label-sm text-[#b4b4b4]">Enterprise Tier</p>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 flex flex-col w-full">
          {NAV_ITEMS.map((item) => {
            const active =
              location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-6 py-3 border-l-2 transition-all duration-200 ease-in-out ${
                  active
                    ? 'text-white border-[#10a37f] bg-[#212121]'
                    : 'text-[#b4b4b4] border-transparent hover:bg-[#212121] hover:text-white'
                }`}
              >
                <span
                  className="material-symbols-outlined text-[20px]"
                  style={active ? { fontVariationSettings: "'FILL' 1" } : undefined}
                >
                  {item.icon}
                </span>
                {item.label}
              </NavLink>
            );
          })}
        </div>

        {/* Bottom Actions */}
        <div className="mt-auto flex flex-col w-full">
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-6 py-3 text-[#b4b4b4] border-l-2 border-transparent hover:bg-[#212121] hover:text-white transition-all duration-200 ease-in-out"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
            Settings
          </NavLink>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="ml-[240px] flex-1 flex flex-col h-full bg-background relative z-0">
        {/* TopNavBar */}
        <header className="h-16 border-b border-[#2f2f2f] bg-[#0d0d0d] flex justify-between items-center px-6 w-full sticky top-0 z-40 font-['Inter'] antialiased tracking-tight">
          <div className="flex items-center">
            <div className="text-lg font-bold text-white tracking-wide">FairLens</div>
            {isDemoMode && (
              <span className="ml-3 px-2 py-0.5 bg-primary/10 text-primary rounded text-[11px] font-medium border border-primary/20">
                DEMO
              </span>
            )}
          </div>
          <div className="flex items-center space-x-md text-[#b4b4b4]">
            <button className="flex items-center justify-center p-1 rounded-full hover:bg-surface-container hover:text-white transition-colors duration-200 active:scale-95">
              <span className="material-symbols-outlined text-[20px]">notifications</span>
            </button>
            <button className="flex items-center justify-center p-1 rounded-full hover:bg-surface-container hover:text-white transition-colors duration-200 active:scale-95">
              <span className="material-symbols-outlined text-[20px]">help_outline</span>
            </button>
            <div className="h-4 border-l border-[#2f2f2f] pl-4 flex items-center gap-md relative" ref={dropdownRef}>
              <span className="text-sm font-medium text-[#b4b4b4] hidden md:block max-w-[150px] truncate">
                {displayName}
              </span>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="w-8 h-8 rounded-full overflow-hidden border border-[#2f2f2f] cursor-pointer active:scale-95 transition-transform bg-primary-container flex items-center justify-center text-on-primary-container text-xs font-bold"
              >
                {user?.photoURL ? (
                  <img src={user.photoURL} alt="" className="w-full h-full object-cover" />
                ) : (
                  initials
                )}
              </button>

              {/* User Dropdown */}
              {showDropdown && (
                <div className="absolute top-full right-0 mt-2 w-64 bg-[#171717] border border-[#2f2f2f] rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden">
                  {/* User info */}
                  <div className="px-4 py-3 border-b border-[#2f2f2f]">
                    <p className="text-white text-sm font-medium truncate">{displayName}</p>
                    <p className="text-[#b4b4b4] text-xs truncate">{displayEmail}</p>
                    {isDemoMode && (
                      <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 bg-primary/10 text-primary rounded text-[10px] font-medium border border-primary/20">
                        <span className="material-symbols-outlined text-[12px]">science</span>
                        Demo Mode Active
                      </span>
                    )}
                  </div>
                  {/* Actions */}
                  <div className="py-1">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-[#b4b4b4] hover:bg-[#212121] hover:text-white transition-colors text-sm text-left"
                    >
                      <span className="material-symbols-outlined text-[18px]">logout</span>
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
