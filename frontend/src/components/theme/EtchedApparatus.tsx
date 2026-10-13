/**
 * 细线刻绘的力学装置：斜面上的滑块（受力分解）、定滑轮与悬挂重物、弹簧振子、抛体轨迹、量角与尺寸线。
 * 每条线带 pathLength=1，样式层用 stroke-dashoffset 1→0 依次画出。纯装饰，读屏忽略。
 */
export default function EtchedApparatus({ className = '' }: { className?: string }) {
  let n = 0;
  // 依次递增的绘制序号，控制每条线的出场延迟
  const d = () => ({ pathLength: 1, style: { ['--n' as string]: n++ } });
  // 带箭头的矢量：箭杆 + 两翼，箭头长 8、半宽 3.5
  const arrow = (x1: number, y1: number, x2: number, y2: number) => {
    const len = Math.hypot(x2 - x1, y2 - y1);
    const ux = (x2 - x1) / len, uy = (y2 - y1) / len;
    const bx = x2 - ux * 8, by = y2 - uy * 8;
    const head = `M${(bx - uy * 3.5).toFixed(1)} ${(by + ux * 3.5).toFixed(1)} L${x2} ${y2} L${(bx + uy * 3.5).toFixed(1)} ${(by - ux * 3.5).toFixed(1)}`;
    return (
      <>
        <path {...d()} className="vec" d={`M${x1} ${y1} L${x2} ${y2}`} />
        <path {...d()} className="vec" d={head} />
      </>
    );
  };

  return (
    <svg className={`etched ${className}`} viewBox="0 0 400 300" aria-hidden="true">
      {/* 地面与地面阴影线 */}
      <path {...d()} d="M14 238 H386" />
      <path {...d()} className="thin" d="M20 238 l-8 9 M36 238 l-8 9 M52 238 l-8 9 M68 238 l-8 9 M84 238 l-8 9 M100 238 l-8 9 M116 238 l-8 9 M132 238 l-8 9 M148 238 l-8 9 M164 238 l-8 9 M180 238 l-8 9 M196 238 l-8 9 M212 238 l-8 9 M228 238 l-8 9 M244 238 l-8 9 M260 238 l-8 9 M276 238 l-8 9 M292 238 l-8 9 M308 238 l-8 9 M324 238 l-8 9 M340 238 l-8 9 M356 238 l-8 9 M372 238 l-8 9" />

      {/* 斜面 30°：底边 40→250，高 121 */}
      <path {...d()} d="M40 238 L250 238 L250 117 Z" />
      <path {...d()} className="thin" d="M84 238 A44 44 0 0 0 78.1 216" />
      <text x="90" y="228">θ</text>

      {/* 滑块：贴在斜面上，中心 (165,153.5)，随斜面转 -30° */}
      <g transform="rotate(-30 165 153.5)">
        <path {...d()} d="M147 142.5 h36 v22 h-36 Z" />
        <path {...d()} className="thin" d="M151 146.5 h28 v14 h-28 Z" />
      </g>
      {/* 受力：重力 mg 向下，支持力 N 沿法向，摩擦 f 沿斜面向下（滑块被 m₂ 拉着上行） */}
      {arrow(165, 153.5, 165, 208)}
      <text x="171" y="206">mg</text>
      {arrow(165, 153.5, 141, 112)}
      <text x="124" y="110">N</text>
      {arrow(149.4, 162.5, 123.4, 177.5)}
      <text x="110" y="190">f</text>
      {/* mg 分解成沿斜面与垂直斜面两个分量 */}
      <path {...d()} className="dash" d="M165 153.5 L188.6 194.4 L165 208" />

      {/* 斜面顶端的定滑轮、绳、悬挂重物 */}
      <circle {...d()} cx="262" cy="108" r="12" />
      <circle {...d()} className="thin" cx="262" cy="108" r="2.5" />
      <path {...d()} className="thin" d="M262 108 L250 117" />
      <path {...d()} d="M181 144.5 L256 97.6" />
      <path {...d()} d="M274 108 V176" />
      <path {...d()} d="M262 176 h24 v26 h-24 Z" />
      <text x="290" y="193">m₂</text>

      {/* 墙与弹簧振子 */}
      <path {...d()} d="M318 238 V186" />
      <path {...d()} className="thin" d="M318 192 l-7 -6 M318 202 l-7 -6 M318 212 l-7 -6 M318 222 l-7 -6 M318 232 l-7 -6" />
      <path {...d()} d="M318 222 h6 l4 -7 l6 14 l6 -14 l6 14 l6 -14 l6 14 l4 -7 h4" />
      <path {...d()} d="M366 210 h18 v28 h-18 Z" />
      <path {...d()} className="dash" d="M375 204 V196 M360 200 h30" />
      <text x="356" y="190">x</text>

      {/* 抛体轨迹与射程尺寸线 */}
      <path {...d()} className="dash" d="M20 64 Q74 -18 132 36" />
      <circle {...d()} className="thin" cx="20" cy="64" r="3" />
      {arrow(20, 64, 40, 34)}
      <text x="42" y="36">v₀</text>
      <path {...d()} className="thin" d="M20 72 V80 M132 72 V80 M20 76 H132" />
      <text x="72" y="92">R</text>

      {/* 右上角：椭圆轨道与焦点 */}
      <ellipse {...d()} cx="338" cy="52" rx="46" ry="26" />
      <ellipse {...d()} className="thin" cx="338" cy="52" rx="30" ry="17" transform="rotate(-18 338 52)" />
      <circle {...d()} className="thin" cx="325" cy="52" r="3.5" />
      <circle {...d()} className="thin" cx="384" cy="52" r="2" />

      {/* 斜面底边尺寸线与标注 */}
      <path {...d()} className="thin" d="M40 262 V270 M250 262 V270 M40 266 H250" />
      <text x="130" y="282">L = 2.0 m</text>
      <text x="176" y="230">μ = 0.25</text>
    </svg>
  );
}
