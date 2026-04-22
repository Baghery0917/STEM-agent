import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { StudentResponse } from '@/api/types';

interface StudentState {
  current: StudentResponse | null;
  setCurrent: (student: StudentResponse | null) => void;
}

export const useStudentStore = create<StudentState>()(
  persist(
    (set) => ({
      current: null,
      setCurrent: (student) => set({ current: student }),
    }),
    {
      name: 'stem:current-student',
    },
  ),
);
