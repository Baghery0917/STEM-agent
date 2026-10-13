type Figure = 'leonard' | 'penny' | 'howard' | 'raj' | 'bernadette' | 'amy' | 'sheldon' | 'stuart';
/** 剪影：八人重复一轮半，铺满整宽，形成人群纵深 */
const ROW: Figure[] = ['stuart', 'raj', 'amy', 'howard', 'penny', 'sheldon', 'bernadette', 'leonard', 'stuart', 'raj', 'amy', 'howard'];
const silhouetteSrc = (k: Figure) => `${import.meta.env.BASE_URL}tbbt/silhouettes/${k}.png`;

interface Props {
  onPractice: () => void;
}

/** 报告页底部：一整排剪影，滚到页底时升起 */
export default function CrowdFooter({ onPractice }: Props) {
  return (
    <footer className="crowd" data-scroll="tail">
      <div className="crowd-copy">
        <div>
          <span className="crowd-kicker">That's the week</span>
          <h3>这周就到这里。</h3>
        </div>
        <button type="button" className="crowd-cta" onClick={onPractice}>开始一组练习 <i>→</i></button>
      </div>
      <div className="crowd-stage" aria-hidden="true">
        <div className="crowd-row back">
          {ROW.map((k, i) => (
            <img key={i} src={silhouetteSrc(k)} alt="" style={{ ['--i' as string]: i }} draggable={false} />
          ))}
        </div>
      </div>
    </footer>
  );
}
