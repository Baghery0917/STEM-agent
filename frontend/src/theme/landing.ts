/** 落地页静态内容。新闻按日期倒序，来源都是公开报道；冷知识带出处或集号。 */

export interface NewsItem {
  date: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  tag: string;
}

export const PHYSICS_NEWS: NewsItem[] = [
  {
    date: '2026-10-06',
    tag: 'Nobel',
    title: '2026 年诺贝尔物理学奖：IceCube 与高能中微子',
    summary: 'Francis Halzen 因「对 IceCube 中微子天文台的决定性贡献，以及发现天体物理起源的高能中微子」获奖。南极冰层被当成探测器，捕捉穿过地球的「幽灵粒子」。',
    source: 'nobelprize.org',
    url: 'https://www.nobelprize.org/prizes/physics/2026/press-release',
  },
  {
    date: '2026-10-06',
    tag: 'Quantum',
    title: '混沌量子行为里找到了反复出现的图案',
    summary: '许多复杂量子系统在组件相互作用后会迅速丢失初态的可辨特征。新研究在这种「看似混沌」里识别出周期性结构，为描述规则运动与混沌运动给出了统一框架。',
    source: 'phys.org',
    url: 'https://phys.org/physics-news',
  },
  {
    date: '2026-10-05',
    tag: 'Plasma',
    title: '激光把空气电离成「光剑」天线，直接发射无线电',
    summary: '研究者用激光在空气里打出一条等离子细丝，当作天线发出 30 MHz 的甚高频信号。没有金属，没有导线，关掉激光天线就消失。',
    source: 'phys.org',
    url: 'https://phys.org/physics-news',
  },
  {
    date: '2026-10-03',
    tag: 'Superconductivity',
    title: '超导临界温度之上仍有库珀对',
    summary: '伊利诺伊大学在二碲化铀中观察到：温度已高于超导转变点，电子仍成对存在，形成「对密度波」。这是一种此前未被归类的超导行为。',
    source: 'phys.org',
    url: 'https://phys.org/physics-news',
  },
  {
    date: '2026-10-02',
    tag: 'Photonics',
    title: '不需要主动控制也能锁频的芯片激光器',
    summary: 'EPFL 做出一款芯片级激光器，在整个测试工作范围内频率保持稳定，不靠电子反馈回路。论文发表于 Nature Photonics。',
    source: 'Nature Photonics',
    url: 'https://phys.org/physics-news',
  },
];

export interface TriviaItem {
  /** 短标题 */
  head: string;
  body: string;
  /** 出处：集号或来源 */
  ref: string;
}

export const TBBT_TRIVIA: TriviaItem[] = [
  {
    head: '白板上的公式都是真的',
    body: '剧组请了 UCLA 物理教授 David Saltzberg 当科学顾问。剧本里写着「[科学待填]」的地方由他补齐，白板上的推导也是他写的，有时还藏着当周的物理新闻。',
    ref: 'NPR · 2013',
  },
  {
    head: '那个位置为什么是那个位置',
    body: '冬天离暖气片近到够暖、又不至于出汗；夏天正好在两扇窗之间的穿堂风路径上；看电视的角度既不正对、又不会产生视差。Sheldon 在第一季就解释清楚了。',
    ref: 'S01E01',
  },
  {
    head: 'Bazinga 其实很稀有',
    body: '按全剧粉丝手打剧本统计，Sheldon 说「Bazinga」只有 23 次，集中在第二到第五季。他自己的定义是：「我很少开玩笑，开玩笑时你会从这个词知道。」',
    ref: 'S03E21 · 语料统计',
  },
  {
    head: '电梯坏了十二年',
    body: '公寓楼的电梯从第一季坏到大结局，原因是 Leonard 的火箭燃料实验。剧终那集它终于修好了，而大家决定还是走楼梯。',
    ref: 'S03E22 · S12E24',
  },
  {
    head: '一位物理学家让主角用了他的研究',
    body: 'Sheldon 解释自己十六岁没学开车时说的那段「N=4 超对称理论中的微扰振幅」，是 Saltzberg 一位同事正在做的真实课题。',
    ref: 'NPR · 2013',
  },
  {
    head: '期中考答案出现在白板上',
    body: 'UCLA 荣誉物理课的学生去片场当观众那天，Saltzberg 把他们当天刚考完的期中答案写在了 Sheldon 的白板上。过了好一会儿才有人发现。',
    ref: 'Deadline · 2013',
  },
  {
    head: 'Soft Kitty 是一首真的摇篮曲',
    body: '这首歌出现在剧里不止一次，Sheldon 生病时 Penny 唱过，后来也用来哄 Sheldon。统计语料，Penny 提到它 11 次，Sheldon 7 次。',
    ref: '语料统计',
  },
  {
    head: '敲门三下是有规则的',
    body: '敲三下、叫一次名字，再重复两轮。Sheldon 解释过这是为了给门里的人留足反应时间。本站登录页的「敲门」就是照这个做的。',
    ref: 'S10E05',
  },
];
