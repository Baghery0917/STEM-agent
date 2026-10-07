/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** 为 '1' 时启用浏览器内假后端与 hash 路由（仅用于静态预览构建） */
  readonly VITE_PREVIEW_MOCK?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
