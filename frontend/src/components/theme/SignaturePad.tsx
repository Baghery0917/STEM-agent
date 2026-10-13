import { useRef, useState, type PointerEvent } from 'react';

/** 签名坐标系，和后端 signature 字段约定一致 */
export const SIGN_W = 260;
export const SIGN_H = 80;

type Pt = [number, number];

/** 笔画点列 → path d：中点二次贝塞尔平滑，一位小数 */
function strokeToPath(pts: Pt[]) {
  const f = (n: number) => n.toFixed(1);
  if (pts.length === 1) return `M${f(pts[0][0])} ${f(pts[0][1])} L${f(pts[0][0] + 0.5)} ${f(pts[0][1])}`;
  let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [x, y] = pts[i];
    const [nx, ny] = pts[i + 1];
    d += ` Q${f(x)} ${f(y)} ${f((x + nx) / 2)} ${f((y + ny) / 2)}`;
  }
  const last = pts[pts.length - 1];
  return `${d} L${f(last[0])} ${f(last[1])}`;
}

/** 一笔一个子路径，按 M 拆开以便逐笔重放 */
export const splitStrokes = (d: string) => d.split(/(?=M)/).map((s) => s.trim()).filter(Boolean);

interface Props {
  value: string;
  onChange: (d: string) => void;
  disabled?: boolean;
}

/** 手写签名板：指针按下开始一笔，抬起结束；输出 SVG path d */
export default function SignaturePad({ value, onChange, disabled }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [live, setLive] = useState<Pt[] | null>(null);

  const toPt = (e: PointerEvent): Pt => {
    const r = svgRef.current!.getBoundingClientRect();
    return [
      Math.min(SIGN_W, Math.max(0, ((e.clientX - r.left) / r.width) * SIGN_W)),
      Math.min(SIGN_H, Math.max(0, ((e.clientY - r.top) / r.height) * SIGN_H)),
    ];
  };

  const down = (e: PointerEvent<SVGSVGElement>) => {
    if (disabled) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    setLive([toPt(e)]);
  };
  const move = (e: PointerEvent<SVGSVGElement>) => {
    if (!live) return;
    const p = toPt(e);
    const [lx, ly] = live[live.length - 1];
    // 小于 0.8 单位的抖动不记，路径更短更顺
    if (Math.hypot(p[0] - lx, p[1] - ly) < 0.8) return;
    setLive([...live, p]);
  };
  const up = () => {
    if (!live) return;
    onChange(`${value} ${strokeToPath(live)}`.trim());
    setLive(null);
  };

  return (
    <div className={`sigpad ${disabled ? 'disabled' : ''}`}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SIGN_W} ${SIGN_H}`}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={up}
        onPointerCancel={up}
        aria-label="签名区域，用鼠标或手指写下名字"
        role="img"
      >
        <line className="baseline" x1="14" y1={SIGN_H - 14} x2={SIGN_W - 14} y2={SIGN_H - 14} />
        {splitStrokes(value).map((d, i) => <path key={i} d={d} />)}
        {live && <path d={strokeToPath(live)} />}
      </svg>
      {!value && !live && <span className="sigpad-hint">在这里签名</span>}
      {value && !disabled && <button type="button" className="sigpad-clear" onClick={() => onChange('')}>重写</button>}
    </div>
  );
}
