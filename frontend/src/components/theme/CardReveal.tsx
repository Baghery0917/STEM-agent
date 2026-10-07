import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { updateStudent } from '@/api/students';
import type { Persona } from '@/api/types';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import { CARD_QUOTE, CARD_SPOT, personaByKey, personaFigure, type PersonaKey } from '@/theme/personas';

interface Props {
  cardKey: PersonaKey;
  onClose: () => void;
}

/** 获卡时刻：全屏翻牌。正面插画加台词，背面可直接选为讲师。 */
export default function CardReveal({ cardKey, onClose }: Props) {
  const p = personaByKey(cardKey);
  const [flipped, setFlipped] = useState(false);
  const student = useStudentStore((s) => s.current)!;
  const setCurrent = useStudentStore((s) => s.setCurrent);
  const qc = useQueryClient();
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => setFlipped(true), 700);
    return () => clearTimeout(t);
  }, []);

  const pick = useMutation({
    mutationFn: () => updateStudent(student.id, { persona: cardKey as Persona }),
    onSuccess: (s) => { setCurrent(s); qc.invalidateQueries({ queryKey: ['students'] }); toast.info(`${p.name} 现在是你的讲师`); onClose(); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="reveal" onClick={onClose}>
      <div className="rwrap" onClick={(e) => e.stopPropagation()}>
        <div className="rtitle">新的认可卡</div>
        <div className={`flip ${flipped ? 'on' : ''}`} style={{ ['--pc' as string]: p.color }}>
          <div className="face back"><span className="atom-mark" /></div>
          <div className="face front">
            <img src={personaFigure(cardKey)} alt="" />
            <div className="kicker">{CARD_SPOT[cardKey].room}</div>
            <h2>{p.name}</h2>
            <p>"{CARD_QUOTE[cardKey]}"</p>
          </div>
        </div>
        <div className="racts">
          <button type="button" className="btn pri" disabled={pick.isPending} onClick={() => pick.mutate()}>选为讲师</button>
          <button type="button" className="btn ghost" onClick={() => { onClose(); navigate('/cards'); }}>去收藏页</button>
          <button type="button" className="btn ghost" onClick={onClose}>先收下</button>
        </div>
      </div>
    </div>
  );
}
