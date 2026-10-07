import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Mode = 'teaching' | 'practice';
export type Theme = 'system' | 'light' | 'dark';

interface UiState {
  mode: Mode;
  theme: Theme;
  cameraEnabled: boolean;
  setMode: (m: Mode) => void;
  setTheme: (t: Theme) => void;
  setCameraEnabled: (v: boolean) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      mode: 'teaching',
      theme: 'system',
      cameraEnabled: false,
      setMode: (mode) => set({ mode }),
      setTheme: (theme) => set({ theme }),
      setCameraEnabled: (cameraEnabled) => set({ cameraEnabled }),
    }),
    { name: 'stem:ui' },
  ),
);

export function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme !== 'system') return theme;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
