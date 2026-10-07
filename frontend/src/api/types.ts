export type QuestionType =
  | 'single_choice'
  | 'multiple_choice'
  | 'fill_blank'
  | 'short_answer'
  | 'calculation';

export type Difficulty = 'easy' | 'medium' | 'hard';
export type Gender = 'male' | 'female' | 'other';
export type PracticeMode = 'focused' | 'general';
export type TeachingSessionStatus = 'active' | 'completed' | 'cancelled';

export type PipelineStatus = 'pending' | 'running' | 'done' | 'failed';
export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageType =
  | 'question_submit'
  | 'llm_analysis'
  | 'student_data'
  | 'strategy'
  | 'reference_search'
  | 'chat';

export interface Timestamps {
  created_at?: string | null;
  updated_at?: string | null;
}

export interface VolumeResponse extends Timestamps {
  id: number;
  title: string;
  description?: string | null;
  order: number;
}

export interface VolumeCreate {
  title: string;
  description?: string | null;
  order?: number;
}

export type VolumeUpdate = Partial<VolumeCreate>;

export interface ChapterResponse extends Timestamps {
  id: number;
  volume_id: number;
  title: string;
  description?: string | null;
  order: number;
}

export interface ChapterCreate {
  volume_id: number;
  title: string;
  description?: string | null;
  order?: number;
}

export type ChapterUpdate = Partial<ChapterCreate>;

export interface SectionResponse extends Timestamps {
  id: number;
  chapter_id: number;
  title: string;
  content?: string | null;
  order: number;
}

export interface SectionCreate {
  chapter_id: number;
  title: string;
  content?: string | null;
  order?: number;
}

export type SectionUpdate = Partial<SectionCreate>;

export interface QuestionResponse extends Timestamps {
  id: number;
  type: QuestionType;
  content: string;
  content_image?: string | null;
  answer: string;
  answer_image?: string | null;
  analysis?: string | null;
  analysis_image?: string | null;
  difficulty: Difficulty;
  knowledge_point_ids: number[];
}

export interface QuestionCreate {
  type: QuestionType;
  content: string;
  content_image?: string | null;
  answer: string;
  answer_image?: string | null;
  analysis?: string | null;
  analysis_image?: string | null;
  difficulty?: Difficulty;
  knowledge_point_ids?: number[];
}

export type QuestionUpdate = Partial<QuestionCreate>;

export interface QuestionListParams {
  skip?: number;
  limit?: number;
  type?: QuestionType;
  difficulty?: Difficulty;
  knowledge_point_ids?: number[];
  volume_id?: number;
  chapter_id?: number;
}

export type ExplainStyle = 'direct' | 'guided' | 'hint';

export interface StudentResponse extends Timestamps {
  id: number;
  name: string;
  gender: Gender;
  explain_style?: ExplainStyle | null;
}

export interface StudentCreate {
  name: string;
  gender: Gender;
}

export type StudentUpdate = Partial<StudentCreate> & { explain_style?: ExplainStyle | null };

export interface TeachingReferenceResponse extends Timestamps {
  id: number;
  message_id: number;
  question_id: number;
  similarity_score?: number | null;
}

export interface TeachingMessageResponse extends Timestamps {
  id: number;
  session_id: number;
  role: MessageRole;
  content: string;
  message_type: MessageType;
  sequence: number;
  references?: TeachingReferenceResponse[];
  facial_value?: number | null;
  text_value?: number | null;
  /** 即时情绪 1=自信 … 5=非常受挫，仅 user 消息有值 */
  emotion_value?: number | null;
  /** 掌握度自评 0 还没懂 / 1 看懂了讲解 / 2 能自己做 / 3 能讲给别人，仅 assistant 消息 */
  self_rating?: number | null;
}

export interface TeachingSessionDetailResponse extends Timestamps {
  id: number;
  student_id: number;
  status: TeachingSessionStatus;
  pipeline_status: PipelineStatus;
  strategy?: string | null;
  ended_at?: string | null;
  source_practice_session_id?: number | null;
  source_question_ids?: number[] | null;
  messages: TeachingMessageResponse[];
}

export interface TeachingSessionSummaryResponse extends Timestamps {
  id: number;
  student_id: number;
  status: TeachingSessionStatus;
  pipeline_status: PipelineStatus;
  strategy?: string | null;
  ended_at?: string | null;
  source_practice_session_id?: number | null;
  source_question_ids?: number[] | null;
  preview?: string | null;
  message_count: number;
}

export interface SubmitQuestionRequest {
  student_id: number;
  question_content: string;
  question_image?: string | null;
  /** 发送瞬间的摄像头单帧 jpeg data URL，仅用于面部情绪识别 */
  frame_base64?: string | null;
  /** 从练习转来：后端把题干、作答、答案拼进第一条消息 */
  source_practice_session_id?: number | null;
  source_question_ids?: number[] | null;
}

export interface RateMessageRequest {
  session_id: number;
  message_id: number;
  rating: number | null;
}

export interface ChatRequest {
  session_id: number;
  message: string;
  frame_base64?: string | null;
}

export interface EndSessionRequest {
  session_id: number;
  mastery_level_delta?: number | null;
}

export interface TeachingChatResponse {
  session_id: number;
  assistant_message: TeachingMessageResponse;
}

export interface PracticeSessionResponse extends Timestamps {
  id: number;
  timed: boolean;
  /** 每题即时反馈；计时模式恒为 false */
  instant_feedback: boolean;
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
  student_id: number;
  total_count: number;
  question_ids: number[];
  starred_question_ids: number[];
  started_at: string;
  ended_at?: string | null;
  skip_count: number;
  correct_count: number;
  wrong_count: number;
}

export interface PracticeItemResponse extends Timestamps {
  id: number;
  practice_session_id: number;
  student_id: number;
  question_id: number;
  user_answer: string;
  sequence: number;
  is_correct: boolean;
  is_skipped: boolean;
  started_at: string;
  ended_at?: string | null;
  duration_seconds?: number | null;
  emotion?: string | null;
  emotion_value?: number | null;
}

export interface PracticeItemWithQuestionResponse extends PracticeItemResponse {
  question?: QuestionResponse | null;
}

export interface PracticeSessionDetailResponse extends PracticeSessionResponse {
  questions: QuestionPublicResponse[];
  items: PracticeItemWithQuestionResponse[];
}

export interface QuestionPublicResponse extends Timestamps {
  id: number;
  type: QuestionType;
  content: string;
  content_image?: string | null;
  difficulty: Difficulty;
  knowledge_point_ids: number[];
}

export interface StartPracticeRequest {
  student_id: number;
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
  question_types?: QuestionType[] | null;
  total_count: number;
  timed: boolean;
  instant_feedback?: boolean;
}

export interface PracticeMatchRequest {
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
  question_types?: QuestionType[] | null;
}

export interface PracticeMatchResponse {
  matched_count: number;
}

export interface StartSessionResponse {
  session: PracticeSessionResponse;
  questions: QuestionPublicResponse[];
}

export interface SubmitAnswerRequest {
  question_id: number;
  user_answer: string;
  duration_seconds?: number | null;
  frame_base64?: string | null;
}

export interface SubmitAnswerResponse {
  item: PracticeItemResponse;
  /** 统一批改模式下为 null */
  is_correct?: boolean | null;
  correct_answer?: string | null;
  analysis?: string | null;
  analysis_image?: string | null;
  session: PracticeSessionResponse;
}

export interface SkipQuestionRequest {
  question_id: number;
  duration_seconds?: number | null;
}

export interface SkipQuestionResponse {
  item: PracticeItemResponse;
  session: PracticeSessionResponse;
}

export interface StarQuestionRequest {
  question_id: number;
  starred: boolean;
}

export type ReportMode = 'recent' | 'all';

export interface KnowledgePointMastery {
  section_id: number;
  section_title: string;
  mastery_level: number;
  correct_count: number;
  total_practice_count: number;
  total_teaching_count: number;
  last_practice_at?: string | null;
  last_teaching_at?: string | null;
  recent_practice_count: number;
  recent_teaching_count: number;
}

export interface EmotionLogEntry {
  section_id: number;
  section_title: string;
  mode: 'teaching' | 'practice';
  session_id?: number | null;
  emotion_value: number;
  emotion: string;
  created_at: string;
}

export interface EmotionDay {
  date: string;
  value?: number | null;
  count: number;
}

export interface StudentReport {
  mode: ReportMode;
  range_start: string;
  range_end: string;
  practice_count: number;
  teaching_count: number;
  answered_count: number;
  correct_count: number;
  knowledge_points: KnowledgePointMastery[];
  emotion_days: EmotionDay[];
  emotion_logs: EmotionLogEntry[];
  summary?: string | null;
}

export interface SessionSearchHit {
  kind: 'teaching' | 'practice';
  id: number;
  title: string;
  snippet: string;
  at: string;
  status: string;
}

export interface SessionSearchResponse {
  q: string;
  hits: SessionSearchHit[];
}

export interface StudentEvaluation {
  student_id: number;
  evaluation?: string | null;
  highlights: string[];
  source: 'mcp' | 'unavailable';
  detail?: string | null;
}
