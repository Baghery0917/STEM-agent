import { useQuery } from '@tanstack/react-query';
import {
  listChapters,
  listSections,
  listVolumes,
} from '@/api/knowledge';
import type { ChapterResponse, SectionResponse, VolumeResponse } from '@/api/types';

export interface KnowledgeTreeData {
  volumes: VolumeResponse[];
  chapters: ChapterResponse[];
  sections: SectionResponse[];
  byVolume: Map<number, ChapterResponse[]>;
  byChapter: Map<number, SectionResponse[]>;
  sectionById: Map<number, SectionResponse>;
  chapterById: Map<number, ChapterResponse>;
  volumeById: Map<number, VolumeResponse>;
}

function buildIndex(
  volumes: VolumeResponse[],
  chapters: ChapterResponse[],
  sections: SectionResponse[],
): KnowledgeTreeData {
  const byVolume = new Map<number, ChapterResponse[]>();
  const byChapter = new Map<number, SectionResponse[]>();
  const sectionById = new Map<number, SectionResponse>();
  const chapterById = new Map<number, ChapterResponse>();
  const volumeById = new Map<number, VolumeResponse>();

  volumes.forEach((v) => volumeById.set(v.id, v));
  chapters.forEach((c) => {
    chapterById.set(c.id, c);
    const arr = byVolume.get(c.volume_id) ?? [];
    arr.push(c);
    byVolume.set(c.volume_id, arr);
  });
  sections.forEach((s) => {
    sectionById.set(s.id, s);
    const arr = byChapter.get(s.chapter_id) ?? [];
    arr.push(s);
    byChapter.set(s.chapter_id, arr);
  });

  for (const arr of byVolume.values()) arr.sort((a, b) => a.order - b.order);
  for (const arr of byChapter.values()) arr.sort((a, b) => a.order - b.order);

  return {
    volumes: [...volumes].sort((a, b) => a.order - b.order),
    chapters,
    sections,
    byVolume,
    byChapter,
    sectionById,
    chapterById,
    volumeById,
  };
}

export function useKnowledgeTree() {
  return useQuery({
    queryKey: ['knowledge-tree'],
    queryFn: async (): Promise<KnowledgeTreeData> => {
      const [volumes, chapters, sections] = await Promise.all([
        listVolumes({ limit: 1000 }),
        listChapters({ limit: 1000 }),
        listSections({ limit: 1000 }),
      ]);
      return buildIndex(volumes, chapters, sections);
    },
    staleTime: 60_000,
  });
}

export function buildSectionPath(
  tree: KnowledgeTreeData,
  sectionId: number,
): string {
  const section = tree.sectionById.get(sectionId);
  if (!section) return `#${sectionId}`;
  const chapter = tree.chapterById.get(section.chapter_id);
  const volume = chapter ? tree.volumeById.get(chapter.volume_id) : undefined;
  const parts = [volume?.title, chapter?.title, section.title].filter(Boolean);
  return parts.join(' / ');
}
