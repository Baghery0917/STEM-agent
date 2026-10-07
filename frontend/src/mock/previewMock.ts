/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * 预览用浏览器内假后端：拦截 window.fetch，对 /api/v1 下的请求返回写死的数据。
 * 只在 VITE_PREVIEW_MOCK=1 的构建里被引入（见 main.tsx），正常开发与生产不包含。
 */

const now = () => new Date().toISOString();
const ago = (h: number) => new Date(Date.now() - h * 3600e3).toISOString();

const students: any[] = [{ id: 1, name: '林小雨', gender: 'female', explain_style: null, persona: 'leonard', created_at: now(), updated_at: now() }];
// 认可卡：预览里已有 Penny，结束一次练习或会话就发下一张
const CARD_ORDER = ['penny', 'howard', 'raj', 'bernadette', 'amy', 'sheldon'];
const cards: any[] = [{ card_key: 'penny', acquired_at: ago(48) }];
const grantNext = () => { const k = CARD_ORDER.find((c) => !cards.some((x) => x.card_key === c)); if (k) cards.push({ card_key: k, acquired_at: now() }); };
// 徽章：预览里已有三枚，指标写死；签到次数每次 +1，到 10 次发 galileo
const BADGE_RULES = [
  ['newton', 'answered', 1], ['galileo', 'logins', 10], ['tycho', 'logins', 50], ['kepler', 'streak_days', 7],
  ['curie', 'longest_minutes', 45], ['faraday', 'longest_minutes', 90], ['einstein', 'total_minutes', 600], ['hawking', 'total_minutes', 3000],
  ['maxwell', 'answered', 200], ['bohr', 'teaching_sessions', 20], ['heisenberg', 'star_asked', 5], ['feynman', 'teach_others', 5],
] as const;
const metrics: Record<string, number> = { logins: 7, answered: 58, teaching_sessions: 6, teach_others: 2, star_asked: 1, longest_minutes: 52, total_minutes: 214, streak_days: 4 };
const badges: any[] = [{ badge_key: 'newton', acquired_at: ago(200) }, { badge_key: 'curie', acquired_at: ago(70) }];
const grantBadges = () => { const fresh: any[] = []; for (const [k, m, th] of BADGE_RULES) if (!badges.some((b) => b.badge_key === k) && metrics[m] >= th) { const b = { badge_key: k, acquired_at: now() }; badges.push(b); fresh.push(b); } return fresh; };
const badgeProgress = () => BADGE_RULES.map(([k, m, th]) => ({ badge_key: k, metric: m, threshold: th, value: metrics[m] }));
const volumes = [{ id: 1, title: '高二物理 · 必修一', description: null, order: 0 }];
const chapters = [
  { id: 1, volume_id: 1, title: '第三章 相互作用', order: 0 },
  { id: 2, volume_id: 1, title: '第二章 匀变速直线运动', order: 1 },
];
const sections = [
  { id: 1, chapter_id: 1, title: '牛顿第二定律', order: 0 },
  { id: 2, chapter_id: 1, title: '摩擦力', order: 1 },
  { id: 3, chapter_id: 2, title: '匀变速直线运动', order: 0 },
  { id: 4, chapter_id: 2, title: '自由落体', order: 1 },
];
const questions: any[] = [
  { id: 101, type: 'single_choice', difficulty: 'medium', knowledge_point_ids: [4], content: '一物体从高处自由下落，最后 1s 内下落的高度是 25m，取 g = 10 m/s²。物体下落的总时间是？\nA. 2 s\nB. 2.5 s\nC. 3 s\nD. 3.5 s', answer: 'C', analysis: '设总时间 t，则 ½g t² − ½g (t−1)² = 25，解得 t = 3 s。' },
  { id: 102, type: 'fill_blank', difficulty: 'easy', knowledge_point_ids: [3], content: '汽车以 2 m/s² 匀加速启动，5 s 末速度为 ______ m/s。', answer: '10', analysis: 'v = at = 2 × 5 = 10 m/s。' },
  { id: 103, type: 'calculation', difficulty: 'hard', knowledge_point_ids: [3], content: '一辆汽车做匀减速直线运动直至停止，最后 2s 内位移 4m，加速度大小 2 m/s²。求停止前倒数第 2 个 1s 内的位移。', answer: '3 m', analysis: '逆向看作初速为零的匀加速：第 1 s 位移 1 m，第 2 s 位移 3 m。' },
  { id: 104, type: 'multiple_choice', difficulty: 'medium', knowledge_point_ids: [1, 2], content: '关于摩擦力，下列说法正确的是：\nA. 摩擦力方向一定与运动方向相反\nB. 静摩擦力方向与相对运动趋势方向相反\nC. 滑动摩擦力大小与正压力成正比\nD. 摩擦力一定是阻力', answer: 'BC', analysis: '摩擦力可以是动力，方向与相对运动（趋势）方向相反。' },
  { id: 105, type: 'single_choice', difficulty: 'easy', knowledge_point_ids: [1], content: '质量 2 kg 的物体受到 6 N 的合外力，其加速度大小为：\nA. 2 m/s²\nB. 3 m/s²\nC. 6 m/s²\nD. 12 m/s²', answer: 'B', analysis: 'a = F/m = 6/2 = 3 m/s²。' },
];
const pub = (q: any) => ({ id: q.id, type: q.type, difficulty: q.difficulty, knowledge_point_ids: q.knowledge_point_ids, content: q.content, content_image: null });

const teachingSessions: any[] = [
  { id: 12, student_id: 1, status: 'active', pipeline_status: 'done', strategy: '先让你自己找错，不直接给答案 · 语气鼓励', persona: 'sheldon', ended_at: null, created_at: ago(1), updated_at: ago(1), source_practice_session_id: null, source_question_ids: null, messages: [
    { id: 1, session_id: 12, role: 'user', message_type: 'question_submit', sequence: 0, content: '一个质量 2kg 的物块放在倾角 30° 的斜面上，μ=0.2，受到沿斜面向上 15N 的拉力。求加速度。我算出来是 2.07 但答案是 1.37，不知道哪里错了。', emotion_value: 3.6, created_at: ago(1) },
    { id: 2, session_id: 12, role: 'system', message_type: 'llm_analysis', sequence: 1, content: 'Identified knowledge points:\n- 1: 牛顿第二定律\n- 2: 摩擦力', created_at: ago(1) },
    { id: 3, session_id: 12, role: 'system', message_type: 'student_data', sequence: 2, content: '摩擦力方向判断近 2 周错 3 次 · 上次学习 4 天前\nSection 1: mastery=0.58', created_at: ago(1) },
    { id: 4, session_id: 12, role: 'system', message_type: 'strategy', sequence: 3, content: 'Strategy: 先让你自己找错，不直接给答案 · 语气鼓励\nReason: 该知识点近期受挫', created_at: ago(1) },
    { id: 5, session_id: 12, role: 'system', message_type: 'reference_search', sequence: 4, content: 'Reference questions:\n#2311 similarity 91%\n#1876 similarity 84%', created_at: ago(1) },
    { id: 6, session_id: 12, role: 'assistant', message_type: 'chat', sequence: 5, self_rating: null, content: '你的过程我看了，受力分解和公式都没问题，差在**摩擦力的方向**。\n\n先别急着看答案，想一下：拉力 15N 沿斜面向上，而重力沿斜面向下的分量是 $mg\\sin30° = 10N$。物块现在有向上运动的趋势，还是向下？\n\n如果它会往上动，摩擦力应该指向哪边？把这一点改掉再算一遍，看看是不是正好 1.37。', created_at: ago(0.98) },
    { id: 7, session_id: 12, role: 'user', message_type: 'chat', sequence: 6, content: '哦，是向上动，所以摩擦力沿斜面向下。重新算：(15 − 10 − 0.2×2×10×cos30°) / 2 ≈ 0.77？还是不对', emotion_value: 2.2, created_at: ago(0.9) },
    { id: 8, session_id: 12, role: 'system', message_type: 'strategy', sequence: 7, content: 'Strategy: 肯定方向判断，核对数值与题干条件\nReason: 学生已自行纠错', created_at: ago(0.9) },
    { id: 9, session_id: 12, role: 'assistant', message_type: 'chat', sequence: 8, self_rating: null, content: '方向这次对了，这是最关键的一步。现在只剩一个数值：$\\cos30° ≈ 0.866$，所以摩擦力是 $0.2 × 20 × 0.866 ≈ 3.46N$。\n\n代进去：$(15 − 10 − 3.46)/2 ≈ 0.77$……你这里算得没错。把原题第二行小字拍清楚一点发我，我们对一下条件。', created_at: ago(0.88) },
  ] },
  { id: 11, student_id: 1, status: 'completed', pipeline_status: 'done', strategy: null, ended_at: ago(26), created_at: ago(27), updated_at: ago(26), source_practice_session_id: null, source_question_ids: null, messages: [
    { id: 20, session_id: 11, role: 'user', message_type: 'question_submit', sequence: 0, content: '弹簧振子的周期为什么与振幅无关？', created_at: ago(27) },
    { id: 21, session_id: 11, role: 'system', message_type: 'llm_analysis', sequence: 1, content: 'Identified knowledge points:\n- 3: 匀变速直线运动', created_at: ago(27) },
    { id: 22, session_id: 11, role: 'assistant', message_type: 'chat', sequence: 2, self_rating: 2, content: '因为回复力与位移成正比，振幅越大，回复力也按同样比例变大，平均速度同步变大，所以来回一趟的时间不变。你可以试着用能量角度再推一遍。', created_at: ago(27) },
  ] },
];
const practiceSessions: any[] = [
  { id: 7, student_id: 1, timed: true, instant_feedback: false, knowledge_point_ids: [3, 4], difficulty_range: ['easy', 'medium'], total_count: 4, question_ids: [101, 102, 103, 104], starred_question_ids: [103], started_at: ago(0.3), ended_at: null, skip_count: 1, correct_count: 1, wrong_count: 0, created_at: ago(0.3), updated_at: ago(0.3),
    items: [
      { id: 1, practice_session_id: 7, student_id: 1, question_id: 101, user_answer: 'C', sequence: 0, is_correct: true, is_skipped: false, started_at: ago(0.3), ended_at: ago(0.29), duration_seconds: 42, emotion: '自信', emotion_value: 1 },
      { id: 2, practice_session_id: 7, student_id: 1, question_id: 102, user_answer: '', sequence: 1, is_correct: false, is_skipped: true, started_at: ago(0.29), ended_at: ago(0.28), duration_seconds: 12 },
    ] },
  { id: 5, student_id: 1, timed: false, instant_feedback: true, knowledge_point_ids: [1, 2], difficulty_range: ['medium'], total_count: 4, question_ids: [104, 101, 102, 103], starred_question_ids: [], started_at: ago(30), ended_at: ago(29.7), skip_count: 1, correct_count: 2, wrong_count: 1, created_at: ago(30), updated_at: ago(29.7),
    items: [
      { id: 3, practice_session_id: 5, student_id: 1, question_id: 104, user_answer: 'BC', sequence: 0, is_correct: true, is_skipped: false, started_at: ago(30), ended_at: ago(30), duration_seconds: 58 },
      { id: 4, practice_session_id: 5, student_id: 1, question_id: 101, user_answer: 'B', sequence: 1, is_correct: false, is_skipped: false, started_at: ago(30), ended_at: ago(30), duration_seconds: 110 },
      { id: 5, practice_session_id: 5, student_id: 1, question_id: 102, user_answer: '10', sequence: 2, is_correct: true, is_skipped: false, started_at: ago(30), ended_at: ago(30), duration_seconds: 22 },
      { id: 6, practice_session_id: 5, student_id: 1, question_id: 103, user_answer: '', sequence: 3, is_correct: false, is_skipped: true, started_at: ago(30), ended_at: ago(30), duration_seconds: 5 },
    ] },
];
const withQ = (it: any) => ({ ...it, question: questions.find((q) => q.id === it.question_id) });
const sessPublic = ({ items: _items, ...s }: any) => s;

const report = (mode: string) => ({
  mode, range_start: ago(24 * 7), range_end: now(), practice_count: 2, teaching_count: 2, answered_count: 6, correct_count: 4,
  knowledge_points: [
    { section_id: 3, section_title: '匀变速直线运动', mastery_level: 0.72, correct_count: 20, total_practice_count: 24, total_teaching_count: 1, recent_practice_count: 24, recent_teaching_count: 1 },
    { section_id: 4, section_title: '自由落体', mastery_level: 0.8, correct_count: 8, total_practice_count: 10, total_teaching_count: 0, recent_practice_count: 10, recent_teaching_count: 0 },
    { section_id: 1, section_title: '牛顿第二定律', mastery_level: 0.58, correct_count: 4, total_practice_count: 6, total_teaching_count: 2, recent_practice_count: 6, recent_teaching_count: 2 },
    { section_id: 2, section_title: '摩擦力', mastery_level: 0.64, correct_count: 9, total_practice_count: 14, total_teaching_count: 0, recent_practice_count: 14, recent_teaching_count: 0 },
  ],
  emotion_days: [0, 1, 2, 3, 4, 5, 6].map((i) => ({ date: new Date(Date.now() - (6 - i) * 864e5).toISOString().slice(0, 10), value: [1.8, 1.5, 3.6, 3.9, 2.2, 1.3, 1.6][i], count: 3 })),
  emotion_logs: [
    { section_id: 1, section_title: '斜面受力分析', mode: 'teaching', session_id: 12, emotion_value: 3.6, emotion: '受挫', created_at: ago(2) },
    { section_id: 3, section_title: '匀变速 · 10 题', mode: 'practice', session_id: 7, emotion_value: 1.2, emotion: '自信', created_at: ago(5) },
    { section_id: 1, section_title: '弹簧振子周期', mode: 'teaching', session_id: 11, emotion_value: 2.0, emotion: '略犹豫', created_at: ago(27) },
    { section_id: 2, section_title: '动量守恒 · 14 题', mode: 'practice', session_id: 5, emotion_value: 3.9, emotion: '受挫', created_at: ago(30) },
  ],
  summary: mode === 'recent' ? '这周你练了 54 题、讲了 4 道。匀变速直线运动从 61% 升到 72%，进步最大。牛顿第二定律连续两次在摩擦力方向上出错，情绪记录显示这两次都偏受挫，建议下次从一道简单题开始回暖。' : null,
});

let nextId = 1000;
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function handle(method: string, path: string, search: URLSearchParams, body: any): Promise<Response> {
  let m: RegExpMatchArray | null;
  if (path === '/students' && method === 'GET') return json(students);
  if (path === '/students' && method === 'POST') { const s = { id: ++nextId, ...body, explain_style: null, persona: null, created_at: now(), updated_at: now() }; students.push(s); return json(s, 201); }
  if ((m = path.match(/^\/students\/(\d+)\/cards$/))) { grantBadges(); return json({ cards, unlocked: ['leonard', ...cards.map((c) => c.card_key)], badges, badge_progress: badgeProgress() }); }
  if ((m = path.match(/^\/students\/(\d+)\/checkin$/))) { metrics.logins += 1; return json({ login_count: metrics.logins, new_badges: grantBadges() }); }
  if ((m = path.match(/^\/students\/(\d+)\/report$/))) { await delay(300); return json(report(search.get('mode') || 'recent')); }
  if ((m = path.match(/^\/students\/(\d+)\/evaluation$/))) {
    await delay(900);
    return json({ student_id: 1, source: 'mcp', highlights: ['匀变速直线运动 ↑', '摩擦力方向需巩固', '受挫时放慢节奏'], evaluation: '这周练习量稳定，匀变速直线运动进步明显；牛顿第二定律连续两次在摩擦力方向上出错且情绪偏受挫，建议下次从一道基础题回暖后再推进。' });
  }
  if ((m = path.match(/^\/students\/(\d+)\/sessions\/search$/))) {
    const kw = (search.get('q') || '').toLowerCase();
    const hits: any[] = [];
    for (const t of teachingSessions) {
      const hit = t.messages.find((x: any) => (x.role === 'user' || x.role === 'assistant') && x.content.toLowerCase().includes(kw));
      if (hit) { const i = hit.content.toLowerCase().indexOf(kw); hits.push({ kind: 'teaching', id: t.id, title: t.messages[0].content.slice(0, 60), snippet: (i > 20 ? '…' : '') + hit.content.replace(/\n/g, ' ').slice(Math.max(0, i - 20), i + 40) + '…', at: t.created_at, status: t.status }); }
    }
    for (const p of practiceSessions) {
      const names = p.knowledge_point_ids.map((id: number) => sections.find((x) => x.id === id)?.title ?? '');
      const matched = names.filter((n: string) => n.toLowerCase().includes(kw));
      if (matched.length) hits.push({ kind: 'practice', id: p.id, title: `${names.slice(0, 2).join('、')} · ${p.total_count} 题`, snippet: matched.join('、'), at: p.started_at, status: p.ended_at ? 'completed' : 'active' });
    }
    hits.sort((a, b) => (b.at > a.at ? 1 : -1));
    return json({ q: kw, hits });
  }
  if (path === '/admin/login') { await delay(300); return body.password === 'admin' ? json({ token: 'preview-admin-token' }) : json({ detail: '口令不正确（预览版口令是 admin）' }, 401); }
  if ((m = path.match(/^\/students\/(\d+)$/)) && method === 'PUT') { const s = students.find((x) => x.id === Number(m![1])); Object.assign(s, body); return json(s); }
  if (path === '/volumes') return json(volumes);
  if (path === '/chapters') return json(chapters);
  if (path === '/sections') return json(sections);

  if (path === '/teaching/sessions' && method === 'GET') {
    return json(teachingSessions.map((s) => ({ ...sessPublic(s), messages: undefined, preview: s.messages[0]?.content.slice(0, 60), message_count: s.messages.length })));
  }
  if (path === '/teaching/sessions' && method === 'POST') {
    const id = ++nextId;
    const content = body.source_practice_session_id
      ? `（来自练习 #${body.source_practice_session_id}）\n\n${(body.source_question_ids ?? [103]).map((qid: number) => { const q = questions.find((x) => x.id === qid) ?? questions[2]; const ps = practiceSessions.find((p) => p.id === body.source_practice_session_id); const pos = ps ? ps.question_ids.indexOf(q.id) + 1 : 1; const it = ps?.items.find((i: any) => i.question_id === q.id); const outcome = !it ? '未作答' : it.is_skipped ? '跳过' : `我的答案：${it.user_answer}（${it.is_correct ? '答对' : '答错'}）`; return `【练习第 ${pos || 1} 题】\n${q.content}\n${outcome}\n正确答案：${q.answer}`; }).join('\n\n')}\n\n${body.question_content}`
      : body.question_content;
    const s: any = { id, student_id: 1, status: 'active', pipeline_status: 'running', strategy: null, persona: students[0].persona, ended_at: null, created_at: now(), updated_at: now(), source_practice_session_id: body.source_practice_session_id ?? null, source_question_ids: body.source_question_ids ?? null, messages: [{ id: ++nextId, session_id: id, role: 'user', message_type: 'question_submit', sequence: 0, content, emotion_value: 2.4, created_at: now() }] };
    teachingSessions.unshift(s);
    const steps: [string, string][] = [
      ['llm_analysis', 'Identified knowledge points:\n- 3: 匀变速直线运动'],
      ['student_data', '本次练习 4 题正确 2 · 该知识点掌握度 72% · 刚答错本题'],
      ['strategy', 'Strategy: 从逆向思维切入，先让学生自己发现「平分位移」为什么不成立\nReason: 刚答错本题'],
      ['reference_search', 'Reference questions:\n#103 similarity 95%'],
    ];
    steps.forEach(([t, c], i) => setTimeout(() => s.messages.push({ id: ++nextId, session_id: id, role: 'system', message_type: t, sequence: i + 1, content: c, created_at: now() }), 900 * (i + 1)));
    setTimeout(() => {
      s.messages.push({ id: ++nextId, session_id: id, role: 'assistant', message_type: 'chat', sequence: 5, self_rating: null, content: body.source_practice_session_id
        ? '我们把这道题倒过来看：汽车停止的瞬间当作起点，往回看就是一个**初速度为零的匀加速运动**。\n\n最后 2 s 的位移 4 m 对应的是「前 2 s」。初速为零的匀加速，第 1 s 和第 2 s 的位移之比是多少？想清楚这个比例，答案就出来了。'
        : '好，先确认一下我的理解：你想解决的是「' + body.question_content.slice(0, 20) + '…」这道题。\n\n先不急着算，你觉得这题考的是哪个知识点？说说你的第一反应。', created_at: now() });
      s.pipeline_status = 'done';
    }, 5000);
    return json(s, 201);
  }
  if (path === '/teaching/sessions/rate') { const s = teachingSessions.find((x) => x.id === body.session_id); const msg = s.messages.find((x: any) => x.id === body.message_id); msg.self_rating = body.rating; return json(msg); }
  if (path === '/teaching/sessions/end') { const s = teachingSessions.find((x) => x.id === body.session_id); s.status = 'completed'; s.ended_at = now(); grantNext(); return json(s); }
  if (path === '/teaching/sessions/chat/stream') {
    const s = teachingSessions.find((x) => x.id === body.session_id);
    s.messages.push({ id: ++nextId, session_id: s.id, role: 'user', message_type: 'chat', sequence: s.messages.length, content: body.message, emotion_value: 1.8, created_at: now() });
    const text = /快|慢|再讲|换/.test(body.message)
      ? '好，我换个讲法。把斜面想成一个倾斜的桌面：物块被往上拉，它「想」往上滑，摩擦力就要拦着它，所以方向沿斜面**向下**。这一步想通了，后面只是算数。'
      : '好，那我们把条件再核一遍。你截图里第二行写的 g 取 9.8 还是 10？这会直接影响第一项。顺便把 μ 的值也再看一眼。';
    const enc = new TextEncoder();
    const stream = new ReadableStream({
      async start(ctrl) {
        for (let i = 0; i < text.length; i += 3) {
          ctrl.enqueue(enc.encode(`data: ${JSON.stringify({ delta: text.slice(i, i + 3) })}\n\n`));
          await delay(45);
        }
        s.messages.push({ id: ++nextId, session_id: s.id, role: 'system', message_type: 'strategy', sequence: s.messages.length, content: 'Strategy: 换用类比\nReason: 学生要求', created_at: now() });
        s.messages.push({ id: ++nextId, session_id: s.id, role: 'assistant', message_type: 'chat', sequence: s.messages.length, self_rating: null, content: text, created_at: now() });
        ctrl.enqueue(enc.encode('event: done\ndata: {}\n\n'));
        ctrl.close();
      },
    });
    return new Response(stream, { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
  }
  if ((m = path.match(/^\/teaching\/sessions\/(\d+)\/cancel$/))) { const s = teachingSessions.find((x) => x.id === Number(m![1])); s.status = 'cancelled'; return json(s); }
  if ((m = path.match(/^\/teaching\/sessions\/(\d+)$/))) { const s = teachingSessions.find((x) => x.id === Number(m![1])); return s ? json(s) : json({ detail: 'Session not found' }, 404); }

  if (path === '/practice/match') { await delay(200); return json({ matched_count: 37 }); }
  if (path === '/practice/sessions' && method === 'GET') return json(practiceSessions.map(sessPublic));
  if (path === '/practice/sessions' && method === 'POST') {
    await delay(400);
    const qs = questions.slice(0, Math.min(body.total_count, questions.length));
    const s: any = { id: ++nextId, student_id: 1, timed: body.timed, instant_feedback: body.timed ? false : body.instant_feedback !== false, knowledge_point_ids: body.knowledge_point_ids, difficulty_range: body.difficulty_range, total_count: qs.length, question_ids: qs.map((q) => q.id), starred_question_ids: [], started_at: now(), ended_at: null, skip_count: 0, correct_count: 0, wrong_count: 0, created_at: now(), updated_at: now(), items: [] };
    practiceSessions.unshift(s);
    return json({ session: sessPublic(s), questions: qs.map(pub) }, 201);
  }
  if ((m = path.match(/^\/practice\/sessions\/(\d+)\/submit$/))) {
    const s = practiceSessions.find((x) => x.id === Number(m![1])); const q = questions.find((x) => x.id === body.question_id);
    const norm = (v: string) => v.trim().toUpperCase().replace(/\s/g, '');
    const ok = q.type === 'multiple_choice' ? [...norm(body.user_answer)].sort().join('') === [...norm(q.answer)].sort().join('') : norm(body.user_answer) === norm(q.answer);
    const item = { id: ++nextId, practice_session_id: s.id, student_id: 1, question_id: q.id, user_answer: body.user_answer, sequence: s.items.length, is_correct: ok, is_skipped: false, started_at: now(), ended_at: now(), duration_seconds: body.duration_seconds ?? null };
    s.items.push(item); if (ok) s.correct_count++; else s.wrong_count++;
    if (!s.instant_feedback) return json({ item: { ...item, is_correct: false }, session: sessPublic(s) });
    return json({ item, is_correct: ok, correct_answer: q.answer, analysis: q.analysis, analysis_image: null, session: sessPublic(s) });
  }
  if ((m = path.match(/^\/practice\/sessions\/(\d+)\/skip$/))) {
    const s = practiceSessions.find((x) => x.id === Number(m![1]));
    const item = { id: ++nextId, practice_session_id: s.id, student_id: 1, question_id: body.question_id, user_answer: '', sequence: s.items.length, is_correct: false, is_skipped: true, started_at: now(), ended_at: now(), duration_seconds: body.duration_seconds ?? null };
    s.items.push(item); s.skip_count++;
    return json({ item, session: sessPublic(s) });
  }
  if ((m = path.match(/^\/practice\/sessions\/(\d+)\/star$/))) {
    const s = practiceSessions.find((x) => x.id === Number(m![1]));
    s.starred_question_ids = body.starred ? [...new Set([...s.starred_question_ids, body.question_id])] : s.starred_question_ids.filter((x: number) => x !== body.question_id);
    return json(sessPublic(s));
  }
  if ((m = path.match(/^\/practice\/sessions\/(\d+)\/end$/))) {
    const s = practiceSessions.find((x) => x.id === Number(m![1])); s.ended_at = now();
    const done = new Set(s.items.map((i: any) => i.question_id));
    for (const qid of s.question_ids) if (!done.has(qid)) { s.items.push({ id: ++nextId, practice_session_id: s.id, student_id: 1, question_id: qid, user_answer: '', sequence: s.items.length, is_correct: false, is_skipped: true, started_at: now(), ended_at: now(), duration_seconds: null }); s.skip_count++; }
    grantNext();
    return json(sessPublic(s));
  }
  if ((m = path.match(/^\/practice\/sessions\/(\d+)$/))) {
    const s = practiceSessions.find((x) => x.id === Number(m![1]));
    return s ? json({ ...sessPublic(s), questions: s.question_ids.map((id: number) => pub(questions.find((q) => q.id === id))), items: s.items.map(withQ) }) : json({ detail: 'Session not found' }, 404);
  }
  return json({ detail: `preview mock: no route ${method} ${path}` }, 404);
}

export function installPreviewMock(base = '/api/v1') {
  const realFetch = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url, location.href);
    const idx = url.pathname.indexOf(base);
    if (idx === -1) return realFetch(input, init);
    const path = url.pathname.slice(idx + base.length);
    const method = (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase();
    let body: any = {};
    const raw = init?.body ?? (input instanceof Request ? await input.text() : undefined);
    if (raw && typeof raw === 'string') { try { body = JSON.parse(raw); } catch { body = {}; } }
    await delay(120);
    return handle(method, path, url.searchParams, body);
  };
}
