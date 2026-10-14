// 不打包剧集录音（版权 + 体积），用 Web Audio 合成八音盒音色现场演奏旋律
type Note = [pitch: number, beats: number];

const C4 = 261.63, D4 = 293.66, E4 = 329.63, F4 = 349.23, G4 = 392.0;

export const SOFT_KITTY_LINES: { lyric: string; notes: Note[] }[] = [
  { lyric: 'Soft kitty, warm kitty,', notes: [[G4, 1], [E4, 1], [E4, 2], [F4, 1], [D4, 1], [D4, 2]] },
  { lyric: 'little ball of fur.', notes: [[C4, 1], [D4, 1], [E4, 1], [F4, 1], [G4, 4]] },
  { lyric: 'Happy kitty, sleepy kitty,', notes: [[G4, .5], [G4, .5], [E4, 1], [E4, 2], [F4, .5], [F4, .5], [D4, 1], [D4, 2]] },
  { lyric: 'purr, purr, purr.', notes: [[C4, 1.5], [E4, 1.5], [C4, 4]] },
];

const BEAT = 0.5;

let ctx: AudioContext | null = null;

/** 播放一遍，onLine 在每句开始时回调（-1 表示结束）；返回停止函数 */
export function playSoftKitty(onLine: (index: number) => void): () => void {
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  ctx ??= new Ctor();
  const ac = ctx;
  void ac.resume();

  const master = ac.createGain();
  master.gain.value = 0.22;
  master.connect(ac.destination);

  const timers: number[] = [];
  let t = ac.currentTime + 0.08;
  SOFT_KITTY_LINES.forEach((line, li) => {
    timers.push(window.setTimeout(() => onLine(li), (t - ac.currentTime) * 1000));
    for (const [freq, beats] of line.notes) {
      const dur = beats * BEAT;
      // 基频 + 两倍频泛音，快起慢衰，听起来像八音盒
      for (const [mul, vol] of [[1, 1], [2, 0.28]] as const) {
        const osc = ac.createOscillator();
        const g = ac.createGain();
        osc.type = mul === 1 ? 'triangle' : 'sine';
        osc.frequency.value = freq * mul;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(vol, t + 0.015);
        g.gain.exponentialRampToValueAtTime(0.001, t + Math.max(0.35, dur * 1.1));
        osc.connect(g).connect(master);
        osc.start(t);
        osc.stop(t + dur * 1.2 + 0.1);
      }
      t += dur;
    }
    t += BEAT * 0.5;
  });
  timers.push(window.setTimeout(() => onLine(-1), (t - ac.currentTime) * 1000));

  return () => {
    timers.forEach(clearTimeout);
    master.gain.cancelScheduledValues(ac.currentTime);
    master.gain.setTargetAtTime(0, ac.currentTime, 0.05);
    window.setTimeout(() => master.disconnect(), 300);
  };
}
