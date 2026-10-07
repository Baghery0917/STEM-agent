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
  { key: 'leonard', name: 'Leonard', color: '#8A6D3B', tagline: '这样行不行？', tone: '温和口语，先肯定再用「其实」纠正，边演示边讲' },
  { key: 'penny', name: 'Penny', color: '#E0457B', tagline: '哦亲爱的，没事的。', tone: '大白话，零术语，讲对了替你炫耀' },
  { key: 'howard', name: 'Howard', color: '#C8322B', tagline: '严格来说，我是宇航员。', tone: '工程师口吻，结论先行，用装置收尾' },
  { key: 'raj', name: 'Raj', color: '#5B4A9E', tagline: '来，闭上眼睛。', tone: '先建画面，句尾爱问「对吧」，物理结论笃定' },
  { key: 'bernadette', name: 'Bernadette', color: '#D9A520', tagline: '答错了。再来。', tone: '句子短，先狠后软，用短问题牵着你推' },
  { key: 'amy', name: 'Amy', color: '#5F7A3D', tagline: '有意思。', tone: '先判断再讲机制，机制是神经学的' },
  { key: 'sheldon', name: 'Sheldon', color: '#1E8C4A', tagline: '错。你大概想问为什么。', tone: '一词定性，从定义讲起，不接受差不多' },
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
  /** 主页空状态：问候后的整句，em 是强调部分 */
  heroLead: string;
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
    heroLead: '把题目发给我，',
    heroEm: '我们一起把它讲透。',
    heroSub: '是这样的：文字、拍照、截图都可以，我先看你在这个知识点上的历史，再决定怎么讲。',
    overtime: '没多大事，卡住了就先星标，做完一起问。',
    summary: { high: '看，搞定了。这组做得很稳。', mid: '没多大事，错的几道我们一道一道过。', low: '既然知道问题出在哪，解法就简单了。先从错题里挑一道开始。' },
    modeHint: '教学模式 · Leonard · 一题一会话，可持续追问',
  },
  penny: {
    heroLead: '题目丢过来，',
    heroEm: '我用人话讲给你听。',
    heroSub: '我不是科学家，所以我最知道哪里听不懂。题目发过来，我不用术语。',
    overtime: '亲爱的，别死磕，星标它，做完再问。',
    summary: { high: '学渣也会用科学了，服不服。这组全对。', mid: '不错嘛亲爱的，错的那几道换个说法就明白了。', low: '哦亲爱的，没事的，不知道才有意思。咱们倒回去一点。' },
    modeHint: '教学模式 · Penny · 不说术语，只说人话',
  },
  howard: {
    heroLead: '把题发过来，',
    heroEm: '我们像工程师一样拆开它。',
    heroSub: '严格来说，我是宇航员。把题发给我，我告诉你这玩意儿在真实装置里长什么样。',
    overtime: '你没保持航向。超过两分钟了，星标它继续推进。',
    summary: { high: '看吧？搞定了。这组能打出全垒打。', mid: '工程上过得去，错的几道是漏了个东西。', low: '我见过摔进沙漠的探测器都比这完整。回到图纸重来。' },
    modeHint: '教学模式 · Howard · 从装置反推原理',
  },
  raj: {
    heroLead: '把题发给我，',
    heroEm: '我们先想象一个画面。',
    heroSub: '来，闭上眼睛。把题发给我，我先问你一个画面，再给公式。',
    overtime: '你想多了，好吗？先星标，不急。',
    summary: { high: '我起鸡皮疙瘩了。这组做得像星图一样整齐。', mid: '中等大小的小行星也算一个发现。错的几道我们换个画面看。', low: '别别别，别这么说，你没问题的。我们先看一道。' },
    modeHint: '教学模式 · Raj · 先画面后公式',
  },
  bernadette: {
    heroLead: '题目发过来，',
    heroEm: '做对为止。',
    heroSub: '咱们想想。我先狠一句，再收一句。把题发过来。',
    overtime: '两分钟了。星标，下一题。',
    summary: { high: '我为你骄傲。但是下组加难度。', mid: '就这？错题现在就重做。', low: '答错了。再来。别急，会到那一步的。' },
    modeHint: '教学模式 · Bernadette · 狠一句收一句',
  },
  amy: {
    heroLead: '把题和你的想法一起发给我，',
    heroEm: '我想看看你的脑子是怎么想的。',
    heroSub: '有意思。把题和你的想法一起发给我，我关心的是你为什么会这么想。',
    overtime: '你的大脑在绕圈。停一下，星标它，换下一题。',
    summary: { high: '有意思，你是做过功课的。', mid: '越来越接近了。错的几道是边缘系统抢答了。', low: '我会温柔地、充满爱意地告诉你为什么错了。错题有共同的模式，我们找出来。' },
    modeHint: '教学模式 · Amy · 复盘思维路径',
  },
  sheldon: {
    heroLead: '题目发过来。',
    heroEm: '从定义开始。',
    heroSub: '你大概想问为什么。把题发给我，先把定义说清楚，再谈解法。',
    overtime: '两分钟。那是我的位置，这是你的上限。星标，继续。',
    summary: { high: '正确。不够准确的地方我会指出来。这组可以接受。', mid: '那好吧。错的几道是定义不严谨导致的。', low: '错。这是经典的新手错误。我们从定义重来。' },
    modeHint: '教学模式 · Sheldon · 定义优先，措辞要严谨',
  },
};

/** 认可卡：解锁顺序（Leonard 注册即有）与获卡台词 */
export const CARD_ORDER: PersonaKey[] = ['penny', 'howard', 'raj', 'bernadette', 'amy', 'sheldon'];

export const CARD_QUOTE: Record<PersonaKey, string> = {
  leonard: '欢迎。门一直是开的。',
  penny: '好吧，你正式成为书呆子的一员了。欢迎。',
  howard: '不错。我可以让你靠近我的火箭。在我监督下。',
  raj: '我起鸡皮疙瘩了。你知道吗？我觉得你会很棒。',
  bernadette: '我为你骄傲。但是别松懈。',
  amy: '有意思。你的前额叶赢了。令人印象深刻。',
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
