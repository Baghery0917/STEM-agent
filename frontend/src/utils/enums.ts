import type { Difficulty, Gender, MessageType, PracticeMode, QuestionType } from '@/api/types';

export const QUESTION_TYPE_LABEL: Record<QuestionType, string> = {
  single_choice: '单选题',
  multiple_choice: '多选题',
  fill_blank: '填空题',
  short_answer: '简答题',
  calculation: '计算题',
};

export const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
};

export const DIFFICULTY_COLOR: Record<Difficulty, string> = {
  easy: 'green',
  medium: 'blue',
  hard: 'volcano',
};

export const GENDER_LABEL: Record<Gender, string> = {
  male: '男',
  female: '女',
  other: '其他',
};

export const PRACTICE_MODE_LABEL: Record<PracticeMode, string> = {
  focused: 'Focused（专注练习）',
  general: 'General（通用练习）',
};

export const MESSAGE_TYPE_LABEL: Record<MessageType, string> = {
  question_submit: '题目提交',
  llm_analysis: '知识点分析',
  student_data: '学生画像',
  strategy: '教学策略',
  reference_search: '相似题检索',
  chat: '对话',
};

export const QUESTION_TYPE_OPTIONS = (Object.keys(QUESTION_TYPE_LABEL) as QuestionType[]).map(
  (value) => ({ value, label: QUESTION_TYPE_LABEL[value] }),
);

export const DIFFICULTY_OPTIONS = (Object.keys(DIFFICULTY_LABEL) as Difficulty[]).map((value) => ({
  value,
  label: DIFFICULTY_LABEL[value],
}));

export const GENDER_OPTIONS = (Object.keys(GENDER_LABEL) as Gender[]).map((value) => ({
  value,
  label: GENDER_LABEL[value],
}));
