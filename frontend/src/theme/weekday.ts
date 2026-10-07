/** 剧中固定日程：每天一个主题，登录页门上和教学页开场都会提到 */
export type WeekdayKey = 'thai' | 'cheesecake' | 'comic' | 'pizza' | 'game' | 'laundry' | 'off';

export interface WeekdayTheme {
  key: WeekdayKey;
  /** 门上的英文 */
  en: string;
  /** 教学页开场的中文一句 */
  zh: string;
}

export const WEEKDAYS: Record<number, WeekdayTheme> = {
  1: { key: 'thai', en: 'Monday · Thai food night', zh: '今天是泰国菜之夜，讲完这题再点外卖。' },
  2: { key: 'cheesecake', en: 'Tuesday · Cheesecake Factory', zh: '今天去芝士蛋糕工厂，先把题做完。' },
  3: { key: 'comic', en: 'Wednesday · New comic book day', zh: '今天漫画店上新，题也上新。' },
  4: { key: 'pizza', en: 'Thursday · Pizza night', zh: '今天是披萨夜，先把题切成几块。' },
  5: { key: 'game', en: 'Friday · Vintage video game night', zh: '今天是复古游戏之夜，这题算一关。' },
  6: { key: 'laundry', en: 'Saturday · Laundry night, 8:15', zh: '今天洗衣夜，八点一刻准时。在那之前讲一题。' },
  0: { key: 'off', en: "Sunday · Sheldon's day off", zh: '今天 Sheldon 休息，你不用。' },
};

export const todayTheme = (d = new Date()) => WEEKDAYS[d.getDay()];
