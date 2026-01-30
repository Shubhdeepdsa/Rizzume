"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { publicApi, TOKEN_KEY } from "@/lib/api-client";
import { useRouter } from "next/navigation";

// -- Types --
interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  [key: string]: any;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // -- Load User on Mount --
  useEffect(() => {
    const initAuth = () => {
      const token = localStorage.getItem(TOKEN_KEY);
      const storedUser = localStorage.getItem("rizzume_user");

      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
          setIsAuthenticated(true);
        } catch (e) {
          console.error("Failed to parse user data", e);
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem("rizzume_user");
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // -- Actions --

  const login = async (email: string, pass: string) => {
    try {
      const res = await publicApi.post("/auth/login", { email, password: pass });
      const { token, user: userData } = res.data;

      // Save
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem("rizzume_user", JSON.stringify(userData));

      // Update State
      setUser(userData);
      setIsAuthenticated(true);
    } catch (err) {
      throw err;
    }
  };

  const signup = async (data: any) => {
    try {
      // 1. Create User
      await publicApi.post("/auth/signup", data);
      
      // 2. Auto-Login (Improve UX)
      await login(data.email, data.password);
    } catch (err) {
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("rizzume_user");
    setUser(null);
    setIsAuthenticated(false);
    router.replace("/auth");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
