"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiRequest } from "./api-client";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  permissions: string[];
  phone: string;
  date_of_birth: string | null;
  gender: string;
  address: string;
  profile_picture?: string | null;
  is_verified?: boolean;
  created_at?: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<AuthUser | null>;
  updateProfile: (updates: Partial<AuthUser>) => Promise<AuthUser>;
  hasPermission: (permission: string) => boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function normalizeUser(user: Partial<AuthUser>): AuthUser {
  return {
    id: user.id ?? 0,
    email: user.email ?? "",
    first_name: user.first_name ?? "",
    last_name: user.last_name ?? "",
    role: user.role ?? "",
    permissions: user.permissions ?? [],
    phone: user.phone ?? "",
    date_of_birth: user.date_of_birth ?? null,
    gender: user.gender ?? "",
    address: user.address ?? "",
    profile_picture: user.profile_picture ?? null,
    is_verified: user.is_verified,
    created_at: user.created_at,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const profile = normalizeUser(await apiRequest<Partial<AuthUser>>("/auth/profile/"));
      setUser(profile);
      return profile;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    const loadProfile = async () => {
      await refreshUser();
      if (active) setIsLoading(false);
    };

    const timer = window.setTimeout(() => { void loadProfile(); }, 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiRequest<{ user: Partial<AuthUser> }>("/auth/login/", {
      method: "POST",
      body: { email, password },
    });
    setUser(normalizeUser(response.user));
    await refreshUser();
  }, [refreshUser]);

  const register = useCallback(async (email: string, password: string, confirmPassword: string) => {
    await apiRequest("/auth/register/", {
      method: "POST",
      body: { email, password, confirm_password: confirmPassword },
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiRequest("/auth/logout/", { method: "POST" });
    } finally {
      setUser(null);
    }
  }, []);

  const updateProfile = useCallback(async (updates: Partial<AuthUser>) => {
    const updated = normalizeUser(await apiRequest<Partial<AuthUser>>("/auth/profile/", {
      method: "PATCH",
      body: updates,
    }));
    setUser(updated);
    return updated;
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
    hasPermission: (permission) => user?.permissions.includes(permission) ?? false,
  }), [user, isLoading, login, register, logout, refreshUser, updateProfile]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
