/** 七位讲师：顺序即解锁顺序。颜色按剧中标志物手定。 */
export type PersonaKey = 'leonard' | 'penny' | 'howard' | 'raj' | 'bernadette' | 'amy' | 'sheldon';

export interface PersonaMeta {
  key: PersonaKey;
  name: string;
  /** 气泡主色 */
  color: string;
  /** 一句英文自我介绍，设置页用 */
  tagline: string;
  /** 一句中文说明：语气是什么样的 */
  tone: string;
}

export const PERSONAS: PersonaMeta[] = [
  { key: 'leonard', name: 'Leonard', color: '#8A6D3B', tagline: "Okay, let's take it one step at a time.", tone: '温和、步骤化，先肯定再纠正' },
  { key: 'penny', name: 'Penny', color: '#E0457B', tagline: 'Okay, in English please.', tone: '大白话，拒绝术语，生活例子' },
  { key: 'howard', name: 'Howard', color: '#C8322B', tagline: "I've been to space.", tone: '工程师口吻，什么都往机器上靠' },
  { key: 'raj', name: 'Raj', color: '#5B4A9E', tagline: "Oh, that's beautiful.", tone: '画面感和类比，语气柔软' },
  { key: 'bernadette', name: 'Bernadette', color: '#D9A520', tagline: "Sweetie, that's wrong.", tone: '语气甜，要求狠' },
  { key: 'amy', name: 'Amy', color: '#5F7A3D', tagline: 'Fascinating.', tone: '复盘你为什么会这么想' },
  { key: 'sheldon', name: 'Sheldon', color: '#1E8C4A', tagline: 'Bazinga.', tone: '高傲，从定义和第一性原理出发' },
];

export const DEFAULT_PERSONA: PersonaKey = 'leonard';

export const personaByKey = (key?: string | null): PersonaMeta =>
  PERSONAS.find((p) => p.key === key) ?? PERSONAS[0];

const base = () => import.meta.env.BASE_URL;
export const personaAvatar = (key: PersonaKey) => `${base()}tbbt/avatars/${key}.png`;
export const personaSilhouette = (key: PersonaKey) => `${base()}tbbt/silhouettes/${key}.png`;
export const personaFigure = (key: PersonaKey) => `${base()}tbbt/characters/${key}.png`;

/** 系统文案由当前讲师配音。英文一句，中文正文。不走 LLM。 */
interface PersonaCopy {
  /** 主页空状态：标题强调句 */
  heroEm: string;
  /** 主页空状态：副标题 */
  heroSub: string;
  /** 计时练习超时提醒（每题超过 2 分钟） */
  overtime: string;
  /** 练习总结第一句，按正确率分三档 */
  summary: { high: string; mid: string; low: string };
  /** 输入框的模式提示 */
  modeHint: string;
}

export const PERSONA_COPY: Record<PersonaKey, PersonaCopy> = {
  leonard: {
    heroEm: '我们一起把它讲透。',
    heroSub: 'One step at a time. 文字、拍照、截图都可以，我先看你在这个知识点上的历史，再决定怎么讲。',
    overtime: "Take your time. 卡住了就先星标，做完一起问。",
    summary: { high: "You've got this. 这组做得很稳。", mid: 'Not bad at all. 错的几道我们一道一道过。', low: "Okay, let's take it one step at a time. 先从错题里挑一道开始。" },
    modeHint: '教学模式 · Leonard · 一题一会话，可持续追问',
  },
  penny: {
    heroEm: '用人话讲给你听。',
    heroSub: 'Okay, in English please. 题目发过来，我不用术语，用你听得懂的方式讲。',
    overtime: 'Sweetie, 别死磕，星标它，做完再问。',
    summary: { high: 'See? Not rocket science. 这组全对的样子像那群书呆子了。', mid: 'Not bad, sweetie. 错的那几道换个说法就明白了。', low: 'Yeah, I got those wrong too the first time. 咱们从头来。' },
    modeHint: '教学模式 · Penny · 不说术语，只说人话',
  },
  howard: {
    heroEm: '像工程师一样拆开它。',
    heroSub: "I've been to space. 把题发给我，我告诉你这玩意儿在真实装置里长什么样。",
    overtime: 'Houston, we have a problem. 超过两分钟了，星标它继续推进。',
    summary: { high: 'NASA would have hired you. Probably. 这组很漂亮。', mid: 'Decent engineering. 错的几道是参数没对上。', low: 'Okay, that is how satellites fall. 我们回到图纸重来。' },
    modeHint: '教学模式 · Howard · 从装置反推原理',
  },
  raj: {
    heroEm: '先想象一个画面。',
    heroSub: 'Think of it like a planet orbiting a star. 把题发给我，我先给你一个画面，再给公式。',
    overtime: 'It is okay, the universe is also confusing. 先星标，不急。',
    summary: { high: 'Oh, that is beautiful. 这组做得像星图一样整齐。', mid: 'Good, my friend. 错的几道我们换个画面看。', low: 'The universe is patient. 我们慢慢来，先看一道。' },
    modeHint: '教学模式 · Raj · 先画面后公式',
  },
  bernadette: {
    heroEm: '做对为止。',
    heroSub: "Sweetie, that's wrong. 把题发过来，我先说甜的，再说狠的。",
    overtime: 'Sweetie, 两分钟了。星标，下一题。',
    summary: { high: 'Aww, good job. 下组加难度。', mid: 'Sweetie, that is not enough. 错题现在就重做。', low: 'Let us try that again, shall we? 全部错题重做一遍。' },
    modeHint: '教学模式 · Bernadette · 甜一句狠一句',
  },
  amy: {
    heroEm: '看看你的脑子是怎么想的。',
    heroSub: 'Fascinating. 把题和你的想法一起发给我，我关心的是你为什么会这么想。',
    overtime: 'Your brain is looping. 停一下，星标它，换下一题。',
    summary: { high: 'Fascinating. 你的思维路径这组很干净。', mid: 'Your brain took a few shortcuts. 我们看看是哪几条。', low: 'Interesting pattern. 错题之间有共同的捷径，我们找出来。' },
    modeHint: '教学模式 · Amy · 复盘思维路径',
  },
  sheldon: {
    heroEm: '从定义开始。',
    heroSub: 'I am not insane; my mother had me tested. 把题发给我，先把定义说清楚，再谈解法。',
    overtime: 'Two minutes. That is my spot, and this is your limit. 星标，继续。',
    summary: { high: 'Correct. Though I would have phrased it with more precision. 这组可以接受。', mid: 'Adequate. 错的几道是定义不严谨导致的。', low: 'The universe disagrees with you. 我们从定义重来。' },
    modeHint: '教学模式 · Sheldon · 定义优先，措辞要严谨',
  },
};
