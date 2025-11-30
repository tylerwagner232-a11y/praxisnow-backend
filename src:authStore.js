// src/authStore.js
import { create } from "zustand";

const BACKEND_URL = "https://praxisnow-backend.onrender.com"; 
// ⬆️ z.B. "https://praxisnow-backend.onrender.com"

export const useAuthStore = create((set) => ({
  user: null,
  loading: false,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const res = await fetch(`${BACKEND_URL}/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        set({ loading: false });
        return { success: false, message: data.message || "Login fehlgeschlagen" };
      }

      set({ user: data.user, loading: false });
      return { success: true, user: data.user };
    } catch (e) {
      set({ loading: false });
      return { success: false, message: "Serverfehler beim Login" };
    }
  },

  register: async (email, password, name) => {
    set({ loading: true });
    try {
      const res = await fetch(`${BACKEND_URL}/register`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });

      const data = await res.json();

      if (!res.ok) {
        set({ loading: false });
        return {
          success: false,
          message: data.message || "Registrierung fehlgeschlagen",
        };
      }

      set({ user: data.user, loading: false });
      return { success: true, user: data.user };
    } catch (e) {
      set({ loading: false });
      return { success: false, message: "Serverfehler bei der Registrierung" };
    }
  },

  logout: async () => {
    try {
      await fetch(`${BACKEND_URL}/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      // ist nicht kritisch
    }
    set({ user: null });
  },

  fetchCurrentUser: async () => {
    set({ loading: true });
    try {
      const res = await fetch(`${BACKEND_URL}/me`, {
        credentials: "include",
      });

      if (!res.ok) {
        set({ user: null, loading: false });
        return;
      }

      const data = await res.json();
      set({ user: data.user || null, loading: false });
    } catch (e) {
      set({ user: null, loading: false });
    }
  },
}));
