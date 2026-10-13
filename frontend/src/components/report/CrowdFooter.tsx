import { personaByKey, type PersonaKey } from '@/theme/personas';

type Figure = PersonaKey | 'stuart';
const ALL: PersonaKey[] = ['leonard', 'penny', 'howard', 'raj', 'bernadette', 'amy', 'sheldon'];
/** 后排剪影：八人重复一轮半，铺满整宽，形成人群纵深 */
const BACK: Figure[] = ['stuart', 'raj', 'amy', 'howard', 'penny', 'sheldon', 'bernadette', 'leonard', 'stuart', 'raj', 'amy', 'howard'];
const base = () => import.meta.env.BASE_URL;
const figureSrc = (k: Figure) => `${base()}tbbt/characters/${k}.png`;
const silhouetteSrc = (k: Figure) => `${base()}tbbt/silhouettes/${k}.png`;

interface Props {
  persona?: string | null;
  onPractice: () => void;
}

/**
 * 报告页底部群像：后排一整排剪影，前排七位讲师，滚到页底时两排以不同速度升起。
 * 当前讲师站前排正中，头顶是他的口头禅。
 */
export default function CrowdFooter({ persona, onPractice }: Props) {
  const lead = (ALL.includes(persona as PersonaKey) ? persona : 'leonard') as PersonaKey;
  const others = ALL.filter((k) => k !== lead);
  const frontRow: PersonaKey[] = [...others.slice(0, 3), lead, ...others.slice(3)];
  const meta = personaByKey(lead);

  return (
    <footer className="crowd" data-scroll="tail" style={{ ['--pc' as string]: meta.color }}>
      <div className="crowd-copy">
        <div>
          <span className="crowd-kicker">That's the week</span>
          <h3>这周就到这里。</h3>
        </div>
        <button type="button" className="crowd-cta" onClick={onPractice}>开始一组练习 <i>→</i></button>
      </div>
      <div className="crowd-stage" aria-hidden="true">
        <div className="crowd-row back">
          {BACK.map((k, i) => (
            <img key={i} src={silhouetteSrc(k)} alt="" style={{ ['--i' as string]: i }} draggable={false} />
          ))}
        </div>
        <div className="crowd-row front">
          {frontRow.map((k, i) => (
            <figure key={k} className={k === lead ? 'lead' : ''} style={{ ['--i' as string]: i }}>
              {k === lead && <figcaption>{meta.tagline}</figcaption>}
              <img src={figureSrc(k)} alt="" draggable={false} />
            </figure>
          ))}
        </div>
      </div>
    </footer>
  );
}
