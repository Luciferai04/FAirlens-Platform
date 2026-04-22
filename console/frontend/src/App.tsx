import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import ModelDetail from "./pages/ModelDetail";
import Incidents from "./pages/Incidents";
import ModelRegistry from "./pages/ModelRegistry";
import Compliance from "./pages/Compliance";
import Login from "./pages/Login";

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route path="/" element={
        user ? <Layout><Dashboard /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="/registry" element={
        user ? <Layout><ModelRegistry /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="/models" element={
        user ? <Layout><ModelRegistry /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="/models/:id" element={
        user ? <Layout><ModelDetail /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="/incidents" element={
        user ? <Layout><Incidents /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="/compliance" element={
        user ? <Layout><Compliance /></Layout> : <Navigate to="/login" replace />
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
