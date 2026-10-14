import { useEffect, useRef, useState } from 'react';
import { SOFT_KITTY_LINES, playSoftKitty } from '@/theme/softKittySong';

/** 错题多时出现在总结页的猫贴纸，点一下唱 Soft Kitty */
export default function KittySticker() {
  const [line, setLine] = useState(-1);
  const stopRef = useRef<(() => void) | null>(null);
  const playing = line >= 0;

  useEffect(() => () => stopRef.current?.(), []);

  const toggle = () => {
    if (stopRef.current) {
      stopRef.current();
      stopRef.current = null;
      setLine(-1);
      return;
    }
    stopRef.current = playSoftKitty((i) => {
      setLine(i);
      if (i < 0) stopRef.current = null;
    });
  };

  return (
    <button
      type="button"
      className={`kitty-sticker ${playing ? 'playing' : ''}`}
      onClick={toggle}
      aria-label={playing ? '停止 Soft Kitty' : '播放 Soft Kitty'}
      title={playing ? '再点一下停止' : '错得有点多？让猫给你唱首歌'}
    >
      <span key={line} className="bubble" aria-live="polite">
        {playing ? SOFT_KITTY_LINES[line].lyric : <>戳一下 <i>♪</i></>}
      </span>
      <img src={`${import.meta.env.BASE_URL}tbbt/illustrations/softkitty-cushion.png`} alt="" draggable={false} />
      {playing && (
        <span className="notes" aria-hidden="true">
          <i>♪</i><i>♫</i><i>♪</i>
        </span>
      )}
    </button>
  );
}
