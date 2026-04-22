import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { Navigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';

export default function Login() {
  const { user, loginWithCredential, loginDemo, loading } = useAuth();
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isSigningIn, setIsSigningIn] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsSigningIn(true);
      try {
        const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        if (!res.ok) throw new Error('Failed to fetch user info');
        const userInfo = await res.json();
        
        loginWithCredential(userInfo, tokenResponse.access_token);
      } catch (err: any) {
        console.error(err);
        setLoginError(err.message || 'Failed to retrieve user information.');
        setIsSigningIn(false);
      }
    },
    onError: (error) => {
      console.error('Google Login Failed', error);
      setLoginError('Sign-in failed or was cancelled.');
      setIsSigningIn(false);
    }
  });

  if (user) {
    return <Navigate to="/" replace />;
  }

  // Since we want to use ID tokens (JWT) which is much cleaner, let's use the actual <GoogleLogin> component
  // which renders the official Google button and returns an ID token directly.
  return (
    <div className="bg-background text-on-surface antialiased min-h-screen flex flex-col items-center justify-center p-md relative overflow-hidden">
      {/* Subtle Background Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Content Container */}
      <main className="w-full max-w-md flex flex-col items-center relative z-10">
        {/* Brand Header */}
        <div className="mb-xl flex flex-col items-center">
          {/* Logo Mark */}
          <div className="w-14 h-14 rounded-xl bg-surface-container border border-outline-variant flex items-center justify-center mb-md shadow-lg">
            <span
              className="material-symbols-outlined text-primary text-[32px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              target
            </span>
          </div>
          {/* Brand Name */}
          <h1 className="font-h1 text-h1 text-on-surface mb-xs">FairLens</h1>
          {/* Tagline */}
          <p className="font-body-md text-body-md text-on-surface-variant text-center max-w-[300px]">
            Enterprise AI Governance &amp; Bias Monitoring Platform
          </p>
        </div>

        {/* Authentication Card */}
        <div className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-lg flex flex-col items-center">
          <h2 className="font-h3 text-h3 text-on-surface mb-2">Sign In</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mb-lg text-center">
            Use your organization's Google Workspace account to access the governance console.
          </p>

          {/* Error Message */}
          {loginError && (
            <div className="w-full bg-error-container/20 border border-error-container text-on-error-container px-4 py-3 rounded-lg mb-md flex items-center gap-2 text-body-md">
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>error</span>
              {loginError}
            </div>
          )}

          <button
            onClick={() => {
              setIsSigningIn(true);
              setLoginError(null);
              googleLogin();
            }}
            disabled={loading || isSigningIn}
            className="w-full flex items-center justify-center gap-md px-lg py-3.5 bg-white border border-[#dadce0] rounded-lg hover:bg-[#f8f9fa] hover:shadow-md transition-all duration-200 group disabled:opacity-50 disabled:cursor-wait"
          >
            {isSigningIn ? (
              <div className="w-5 h-5 border-2 border-[#4285F4] border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25C22.56 11.47 22.49 10.72 22.36 10H12V14.26H17.92C17.66 15.63 16.88 16.79 15.71 17.57V20.34H19.28C21.36 18.42 22.56 15.6 22.56 12.25Z" fill="#4285F4" />
                <path d="M12 23C14.97 23 17.46 22.02 19.28 20.34L15.71 17.57C14.73 18.23 13.48 18.63 12 18.63C9.14 18.63 6.71 16.7 5.84 14.1H2.18V16.94C4.01 20.57 7.72 23 12 23Z" fill="#34A853" />
                <path d="M5.84 14.1C5.62 13.44 5.49 12.74 5.49 12C5.49 11.26 5.62 10.56 5.84 9.9V7.06H2.18C1.43 8.55 1 10.22 1 12C1 13.78 1.43 15.45 2.18 16.94L5.84 14.1Z" fill="#FBBC05" />
                <path d="M12 5.38C13.62 5.38 15.06 5.94 16.21 7.02L19.36 3.87C17.45 2.09 14.97 1 12 1C7.72 1 4.01 3.43 2.18 7.06L5.84 9.9C6.71 7.3 9.14 5.38 12 5.38Z" fill="#EA4335" />
              </svg>
            )}
            <span className="font-medium text-[15px] text-[#3c4043]">
              {isSigningIn ? 'Signing in...' : 'Sign in with Google'}
            </span>
          </button>

          {/* Divider */}
          <div className="w-full flex items-center gap-4 my-md">
            <div className="flex-1 h-px bg-outline-variant" />
            <span className="font-label-sm text-label-sm text-on-surface-variant">or</span>
            <div className="flex-1 h-px bg-outline-variant" />
          </div>

          {/* Demo Mode Button */}
          <button
            onClick={() => loginDemo()}
            className="w-full flex items-center justify-center gap-md px-lg py-3 bg-surface border border-outline-variant rounded-lg hover:bg-surface-container-high hover:border-primary/30 transition-all duration-200"
          >
            <span className="material-symbols-outlined text-primary text-[20px]">science</span>
            <span className="font-body-md text-body-md text-on-surface">
              Enter Demo Mode
            </span>
          </button>
          <p className="font-label-sm text-label-sm text-on-surface-variant mt-2 text-center">
            Demo mode provides full access with sample data — no sign-in required.
          </p>

          {/* Security Note */}
          <div className="mt-lg flex items-center justify-center gap-xs text-on-surface-variant opacity-80">
            <span className="material-symbols-outlined text-[16px]">lock</span>
            <span className="font-label-sm text-label-sm">Secure SSO via Google Cloud IAM</span>
          </div>
        </div>

        {/* Footer Links */}
        <footer className="mt-xl flex items-center justify-center gap-lg">
          <a className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors duration-200" href="#">
            Privacy Policy
          </a>
          <span className="w-[3px] h-[3px] rounded-full bg-outline-variant"></span>
          <a className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors duration-200" href="#">
            Terms of Service
          </a>
        </footer>
      </main>
    </div>
  );
}
