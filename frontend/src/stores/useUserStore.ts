import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface UserState {
  currentUser: User | null;
  token: string | null;
  setCurrentUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

/**
 * User state store
 * Manages current user information and authentication token
 * Persisted to localStorage for session management
 */
export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      currentUser: null,
      token: null,

      setCurrentUser: (user) => set({ currentUser: user }),

      setToken: (token) => set({ token }),

      logout: () =>
        set({
          currentUser: null,
          token: null,
        }),
    }),
    {
      name: 'user-storage', // localStorage key
      partialize: (state) => ({
        currentUser: state.currentUser,
        token: state.token,
      }),
    }
  )
);
