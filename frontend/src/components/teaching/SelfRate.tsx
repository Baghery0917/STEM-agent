const LABELS = ['还没懂', '看懂了讲解', '能自己做', '能讲给别人'];

interface Props {
  value: number | null | undefined;
  onChange: (v: number | null) => void;
  disabled?: boolean;
}

/** 依附在最新一条 AI 回复下的选填自评小条 */
export default function SelfRate({ value, onChange, disabled }: Props) {
  const filled = value != null;
  return (
    <div className={`selfrate ${filled ? 'filled' : ''}`}>
      <span className="q">
        到这里，这道题你掌握得怎么样？<span className="opt-tag">选填</span>
      </span>
      <div className="pills">
        {LABELS.map((l, i) => (
          <button
            type="button"
            key={l}
            className={value === i ? 'on' : ''}
            disabled={disabled}
            onClick={() => onChange(value === i ? null : i)}
          >
            {l}
          </button>
        ))}
      </div>
      <span className="state">{filled ? '已记录 · 再点一次取消' : '未填 · 不影响档案'}</span>
    </div>
  );
}
