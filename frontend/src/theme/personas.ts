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
  { key: 'leonard', name: 'Leonard', color: '#8A6D3B', tagline: '好，我们一步一步来。', tone: '温和、步骤化，先肯定再纠正' },
  { key: 'penny', name: 'Penny', color: '#E0457B', tagline: '说人话。', tone: '大白话，拒绝术语，生活例子' },
  { key: 'howard', name: 'Howard', color: '#C8322B', tagline: '我上过太空。', tone: '工程师口吻，什么都往机器上靠' },
  { key: 'raj', name: 'Raj', color: '#5B4A9E', tagline: '啊，真美。', tone: '画面感和类比，语气柔软' },
  { key: 'bernadette', name: 'Bernadette', color: '#D9A520', tagline: '亲爱的，错了。', tone: '语气甜，要求狠' },
  { key: 'amy', name: 'Amy', color: '#5F7A3D', tagline: '有意思。', tone: '复盘你为什么会这么想' },
  { key: 'sheldon', name: 'Sheldon', color: '#1E8C4A', tagline: '逗你玩的。', tone: '高傲，从定义和第一性原理出发' },
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
    heroSub: '一步一步来。文字、拍照、截图都可以，我先看你在这个知识点上的历史，再决定怎么讲。',
    overtime: '不急，卡住了就先星标，做完一起问。',
    summary: { high: '你可以的，这组做得很稳。', mid: '不错了，错的几道我们一道一道过。', low: '好，我们一步一步来，先从错题里挑一道开始。' },
    modeHint: '教学模式 · Leonard · 一题一会话，可持续追问',
  },
  penny: {
    heroEm: '用人话讲给你听。',
    heroSub: '说人话。题目发过来，我不用术语，用你听得懂的方式讲。',
    overtime: '亲爱的，别死磕，星标它，做完再问。',
    summary: { high: '看吧，又不是造火箭。这组全对，像那群书呆子了。', mid: '不错啊亲爱的，错的那几道换个说法就明白了。', low: '这几题我第一次也错了，咱们从头来。' },
    modeHint: '教学模式 · Penny · 不说术语，只说人话',
  },
  howard: {
    heroEm: '像工程师一样拆开它。',
    heroSub: '我上过太空。把题发给我，我告诉你这玩意儿在真实装置里长什么样。',
    overtime: '休斯顿，我们有麻烦了。超过两分钟了，星标它继续推进。',
    summary: { high: 'NASA 可能会要你。可能。这组很漂亮。', mid: '工程上过得去，错的几道是参数没对上。', low: '卫星就是这么掉下来的。我们回到图纸重来。' },
    modeHint: '教学模式 · Howard · 从装置反推原理',
  },
  raj: {
    heroEm: '先想象一个画面。',
    heroSub: '把它想成一颗绕着恒星转的行星。把题发给我，我先给你一个画面，再给公式。',
    overtime: '没关系，宇宙也让人困惑。先星标，不急。',
    summary: { high: '啊，真美。这组做得像星图一样整齐。', mid: '好的朋友，错的几道我们换个画面看。', low: '宇宙很有耐心。我们慢慢来，先看一道。' },
    modeHint: '教学模式 · Raj · 先画面后公式',
  },
  bernadette: {
    heroEm: '做对为止。',
    heroSub: '亲爱的，先说甜的，再说狠的。把题发过来。',
    overtime: '亲爱的，两分钟了。星标，下一题。',
    summary: { high: '哎呀，真棒。下组加难度。', mid: '亲爱的，这还不够。错题现在就重做。', low: '再来一遍，好吗？全部错题重做一遍。' },
    modeHint: '教学模式 · Bernadette · 甜一句狠一句',
  },
  amy: {
    heroEm: '看看你的脑子是怎么想的。',
    heroSub: '有意思。把题和你的想法一起发给我，我关心的是你为什么会这么想。',
    overtime: '你的大脑在绕圈。停一下，星标它，换下一题。',
    summary: { high: '有意思，你这组的思维路径很干净。', mid: '你的大脑抄了几条近道，我们看看是哪几条。', low: '有趣的模式。错题之间有共同的近道，我们找出来。' },
    modeHint: '教学模式 · Amy · 复盘思维路径',
  },
  sheldon: {
    heroEm: '从定义开始。',
    heroSub: '我没疯，我妈带我做过检查。把题发给我，先把定义说清楚，再谈解法。',
    overtime: '两分钟。那是我的位置，这是你的上限。星标，继续。',
    summary: { high: '正确。不过换我会说得更精确。这组可以接受。', mid: '勉强。错的几道是定义不严谨导致的。', low: '宇宙不同意你。我们从定义重来。' },
    modeHint: '教学模式 · Sheldon · 定义优先，措辞要严谨',
  },
};

/** 认可卡：解锁顺序（Leonard 注册即有）与获卡台词 */
export const CARD_ORDER: PersonaKey[] = ['penny', 'howard', 'raj', 'bernadette', 'amy', 'sheldon'];

export const CARD_QUOTE: Record<PersonaKey, string> = {
  leonard: '欢迎。门一直是开的。',
  penny: '好吧，你正式成为书呆子的一员了。欢迎。',
  howard: '不错。我可以让你靠近我的火箭。在我监督下。',
  raj: '你知道吗？我觉得你会很棒。',
  bernadette: '哎呀，我为你骄傲。现在别松懈。',
  amy: '你的神经通路显然重组过了。令人印象深刻。',
  sheldon: '你可以坐我的位置。一次。只限今天。逗你玩的，不可以。',
};

/** 收藏页：每位讲师落在户型图上的房间，百分比坐标 */
export const CARD_SPOT: Record<PersonaKey, { x: number; y: number; room: string }> = {
  leonard: { x: 50.8, y: 60.1, room: '4A 客厅沙发' },
  penny: { x: 25.4, y: 37.1, room: '4B 客厅' },
  howard: { x: 67.4, y: 65.2, room: '4A 厨房' },
  raj: { x: 59.6, y: 49.9, room: '4A 书桌' },
  bernadette: { x: 43.9, y: 25.6, room: '4B 卧室' },
  amy: { x: 39.1, y: 48.6, room: '4A 走廊' },
  sheldon: { x: 85.9, y: 69.1, room: 'Sheldon 的卧室' },
};
