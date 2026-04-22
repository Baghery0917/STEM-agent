import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStudentStore } from '@/stores/studentStore';

export function useRequireStudent() {
  const student = useStudentStore((s) => s.current);
  const navigate = useNavigate();

  useEffect(() => {
    if (!student) {
      navigate('/login', { replace: true });
    }
  }, [student, navigate]);

  return student;
}
