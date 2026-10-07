import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Mode = 'teaching' | 'practice';

interface UiState {
  mode: Mode;
  cameraEnabled: boolean;
  setMode: (m: Mode) => void;
  setCameraEnabled: (v: boolean) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      mode: 'teaching',
      cameraEnabled: false,
      setMode: (mode) => set({ mode }),
      setCameraEnabled: (cameraEnabled) => set({ cameraEnabled }),
    }),
    { name: 'stem:ui' },
  ),
);

