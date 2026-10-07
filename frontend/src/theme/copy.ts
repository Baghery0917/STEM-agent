/** 生活大爆炸主题文案。英文只做点缀，讲题与功能文案全部中文。 */

/** 主页问候的英文副标题，按星期切换（剧中固定日程） */
export const WEEKDAY_LINES: Record<number, string> = {
  0: "Sunday. Even Sheldon takes a break. You don't have to.",
  1: 'Monday is Thai food night. Bring your own chopsticks.',
  2: 'Tuesday: Cheesecake Factory night. Order the physics.',
  3: 'Wednesday is new comic book day. Also, new problems.',
  4: 'Thursday is pizza night. Slice the problem first.',
  5: 'Friday: vintage video game night. Level up.',
  6: 'Saturday is laundry night, 8:15 sharp. Be punctual.',
};


export const LOGIN = {
  title: 'Apartment 4A',
  subtitle: '报上名字敲门。登记过的直接进，第一次来会先登记。',
  teacherTab: 'Roommate Agreement',
  teacherSub: '签署室友协议进入管理台：知识树、题库、学生、数据库',
  passwordPlaceholder: 'Section 7, Clause B',
  outOfOrder: 'ELEVATOR OUT OF ORDER · 请走楼梯',
};

export const EMPTY = {
  sessions: '还没有会话。先发一道题，或者开始一组练习。',
  kitty: 'Soft kitty, warm kitty, little ball of fur.',
};

export const NOT_FOUND = {
  title: 'This page both exists and does not.',
  body: '打开箱子之前，谁也说不准。回到教学页重新开始。',
};

export const TRACE = {
  running: '正在分析',
  done: '分析完成',
  failed: '分析中断，已给出兜底回复',
};
