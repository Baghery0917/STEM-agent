import { apiClient } from './client';
import type {
  ChapterCreate,
  ChapterResponse,
  ChapterUpdate,
  SectionCreate,
  SectionResponse,
  SectionUpdate,
  VolumeCreate,
  VolumeResponse,
  VolumeUpdate,
} from './types';

export async function listVolumes(params?: { skip?: number; limit?: number }) {
  const { data } = await apiClient.get<VolumeResponse[]>('/volumes', { params });
  return data;
}

export async function getVolume(id: number) {
  const { data } = await apiClient.get<VolumeResponse>(`/volumes/${id}`);
  return data;
}

export async function createVolume(body: VolumeCreate) {
  const { data } = await apiClient.post<VolumeResponse>('/volumes', body);
  return data;
}

export async function updateVolume(id: number, body: VolumeUpdate) {
  const { data } = await apiClient.put<VolumeResponse>(`/volumes/${id}`, body);
  return data;
}

export async function deleteVolume(id: number) {
  await apiClient.delete(`/volumes/${id}`);
}

export async function listChaptersByVolume(volumeId: number) {
  const { data } = await apiClient.get<ChapterResponse[]>(`/volumes/${volumeId}/chapters`);
  return data;
}

export async function listChapters(params?: { skip?: number; limit?: number }) {
  const { data } = await apiClient.get<ChapterResponse[]>('/chapters', { params });
  return data;
}

export async function getChapter(id: number) {
  const { data } = await apiClient.get<ChapterResponse>(`/chapters/${id}`);
  return data;
}

export async function createChapter(body: ChapterCreate) {
  const { data } = await apiClient.post<ChapterResponse>('/chapters', body);
  return data;
}

export async function updateChapter(id: number, body: ChapterUpdate) {
  const { data } = await apiClient.put<ChapterResponse>(`/chapters/${id}`, body);
  return data;
}

export async function deleteChapter(id: number) {
  await apiClient.delete(`/chapters/${id}`);
}

export async function listSectionsByChapter(chapterId: number) {
  const { data } = await apiClient.get<SectionResponse[]>(`/chapters/${chapterId}/sections`);
  return data;
}

export async function listSections(params?: { skip?: number; limit?: number }) {
  const { data } = await apiClient.get<SectionResponse[]>('/sections', { params });
  return data;
}

export async function getSection(id: number) {
  const { data } = await apiClient.get<SectionResponse>(`/sections/${id}`);
  return data;
}

export async function createSection(body: SectionCreate) {
  const { data } = await apiClient.post<SectionResponse>('/sections', body);
  return data;
}

export async function updateSection(id: number, body: SectionUpdate) {
  const { data } = await apiClient.put<SectionResponse>(`/sections/${id}`, body);
  return data;
}

export async function deleteSection(id: number) {
  await apiClient.delete(`/sections/${id}`);
}

export interface BulkImportVolume {
  name: string;
  description?: string;
  chapters?: BulkImportChapter[];
}

export interface BulkImportChapter {
  name: string;
  description?: string;
  sections?: BulkImportSection[];
}

export interface BulkImportSection {
  name: string;
  description?: string;
}

export interface BulkImportResult {
  volumesCreated: number;
  chaptersCreated: number;
  sectionsCreated: number;
  errors: Array<{ path: string; message: string }>;
}

// TODO: 后端未实现 POST /volumes/import，当前用顺序 POST 兼容
export async function bulkImportKnowledge(payload: {
  volumes: BulkImportVolume[];
}): Promise<BulkImportResult> {
  const result: BulkImportResult = {
    volumesCreated: 0,
    chaptersCreated: 0,
    sectionsCreated: 0,
    errors: [],
  };

  for (const [vIdx, vol] of payload.volumes.entries()) {
    try {
      const v = await createVolume({
        title: vol.name,
        description: vol.description,
        order: vIdx,
      });
      result.volumesCreated += 1;
      for (const [cIdx, chap] of (vol.chapters ?? []).entries()) {
        try {
          const c = await createChapter({
            volume_id: v.id,
            title: chap.name,
            description: chap.description,
            order: cIdx,
          });
          result.chaptersCreated += 1;
          for (const [sIdx, sec] of (chap.sections ?? []).entries()) {
            try {
              await createSection({
                chapter_id: c.id,
                title: sec.name,
                content: sec.description,
                order: sIdx,
              });
              result.sectionsCreated += 1;
            } catch (e) {
              result.errors.push({
                path: `volumes[${vIdx}].chapters[${cIdx}].sections[${sIdx}]`,
                message: (e as Error).message,
              });
            }
          }
        } catch (e) {
          result.errors.push({
            path: `volumes[${vIdx}].chapters[${cIdx}]`,
            message: (e as Error).message,
          });
        }
      }
    } catch (e) {
      result.errors.push({ path: `volumes[${vIdx}]`, message: (e as Error).message });
    }
  }

  return result;
}
