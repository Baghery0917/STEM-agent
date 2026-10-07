interface Props {
  /** 已完成的步骤数（0–3），对应点亮的轨道数；不传则纯旋转 */
  lit?: number;
  size?: number;
  className?: string;
}

/** 片头转场的原子轨道：三条椭圆轨道旋转，步骤完成时依次点亮 */
export default function AtomSpinner({ lit, size = 16, className }: Props) {
  const orbits = [0, 60, 120];
  return (
    <svg
      className={`atom ${className ?? ''}`}
      width={size}
      height={size}
      viewBox="0 0 40 40"
      aria-hidden="true"
      style={{ ['--atom-size' as string]: `${size}px` }}
    >
      <g className="atom-orbits">
        {orbits.map((deg, i) => (
          <ellipse
            key={deg}
            className={`atom-orbit ${lit != null && i < lit ? 'lit' : ''}`}
            cx="20" cy="20" rx="17" ry="6.5"
            transform={`rotate(${deg} 20 20)`}
          />
        ))}
      </g>
      <circle className="atom-core" cx="20" cy="20" r="3" />
    </svg>
  );
}
