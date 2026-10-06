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

export interface StudentResponse extends Timestamps {
  id: number;
  name: string;
  gender: Gender;
}

export interface StudentCreate {
  name: string;
  gender: Gender;
}

export type StudentUpdate = Partial<StudentCreate>;

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
}

export interface TeachingSessionDetailResponse extends Timestamps {
  id: number;
  student_id: number;
  status: TeachingSessionStatus;
  pipeline_status: PipelineStatus;
  strategy?: string | null;
  ended_at?: string | null;
  messages: TeachingMessageResponse[];
}

export interface TeachingSessionSummaryResponse extends Timestamps {
  id: number;
  student_id: number;
  status: TeachingSessionStatus;
  pipeline_status: PipelineStatus;
  strategy?: string | null;
  ended_at?: string | null;
  preview?: string | null;
  message_count: number;
}

export interface SubmitQuestionRequest {
  student_id: number;
  question_content: string;
  question_image?: string | null;
  /** 发送瞬间的摄像头单帧 jpeg data URL，仅用于面部情绪识别 */
  frame_base64?: string | null;
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
  mode: PracticeMode;
  knowledge_point_ids: number[];
  difficulty_range: string[];
  student_id: number;
  total_count: number;
  started_at: string;
  ended_at?: string | null;
  skip_count: number;
  correct_count: number;
  wrong_count: number;
  skipped_question_ids: number[];
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
  emotion?: string | null;
}

export interface PracticeItemWithQuestionResponse extends PracticeItemResponse {
  question?: QuestionResponse | null;
}

export interface PracticeSessionDetailResponse extends PracticeSessionResponse {
  items: PracticeItemWithQuestionResponse[];
}

export interface StartFocusedRequest {
  student_id: number;
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
  total_count: number;
}

export interface StartGeneralRequest {
  student_id: number;
  knowledge_point_ids: number[];
  difficulty_range: Difficulty[];
}

export interface StartSessionResponse {
  session: PracticeSessionResponse;
  question: QuestionResponse;
}

export interface SubmitAnswerRequest {
  question_id: number;
  user_answer: string;
  emotion?: string | null;
}

export interface SubmitAnswerResponse {
  item: PracticeItemResponse;
  is_correct: boolean;
  next_question: QuestionResponse | null;
}

export interface SkipQuestionRequest {
  question_id: number;
}

export interface NextQuestionResponse {
  question: QuestionResponse | null;
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
}

export interface EmotionLog {
  section_id: number;
  section_title: string;
  emotion: string;
  mode: 'teaching' | 'practice';
  created_at: string;
}

export interface StudentReport {
  mode: ReportMode;
  active_knowledge_points: KnowledgePointMastery[];
  emotion_logs: EmotionLog[];
}
