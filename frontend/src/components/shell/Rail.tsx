import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { useStudentStore } from '@/stores/studentStore';
import { useRailItems, type RailItem } from '@/hooks/useSessionLists';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { useDebounced } from '@/hooks/useDebounced';
import { searchSessions } from '@/api/reports';
import { groupLabel, shortTime } from '@/utils/time';
import { IconAtom, IconCouch, IconKey, IconThermostat, IconWhiteboard } from '@/components/theme/Icons';
import { EMPTY } from '@/theme/copy';
import SoftKitty from '@/components/theme/SoftKitty';
import PersonaAvatar from '@/components/theme/PersonaAvatar';
import BrandMark from '@/components/theme/BrandMark';
import { personaByKey } from '@/theme/personas';

const GROUP_ORDER = ['今天', '昨天', '过去 7 天', '更早'] as const;

export default function Rail() {
  const student = useStudentStore((s) => s.current);
  const navigate = useNavigate();
  const location = useLocation();
  const { items } = useRailItems(student?.id);
  const tree = useKnowledgeTree();
  const [q, setQ] = useState('');
  const debounced = useDebounced(q.trim(), 250);

  // 搜索走后端：教学按消息全文，练习按知识点名
  const search = useQuery({
    queryKey: ['session-search', student?.id, debounced],
    queryFn: () => searchSessions(student!.id, debounced),
    enabled: !!student && debounced.length > 0,
    staleTime: 10_000,
  });

  const groups = useMemo(() => {
    const map = new Map<string, RailItem[]>();
    for (const it of items) {
      const g = groupLabel(it.at);
      map.set(g, [...(map.get(g) ?? []), it]);
    }
    return GROUP_ORDER.filter((g) => map.has(g)).map((g) => [g, map.get(g)!] as const);
  }, [items]);

  const activeKey = location.pathname;
  const isReport = activeKey.startsWith('/report');
  const isSettings = activeKey.startsWith('/settings');
  const isCards = activeKey.startsWith('/cards');
  const searching = debounced.length > 0;
  const newSessionMode = activeKey.startsWith('/practice') ? 'practice' : activeKey.startsWith('/teaching') ? 'teaching' : 'teaching';

  const newSession = () => navigate(newSessionMode === 'practice' ? '/practice/new' : '/teaching');

  return (
    <aside className="rail">
      <div className="brand">
        <BrandMark size={30} />
        <b className="wordmark"><span className="w1">STEM</span><span className="w2">Agent</span></b>
        <span className="ver">{student?.name ?? ''}</span>
      </div>
      <button type="button" className="new-btn" onClick={newSession}>
        <span>＋</span>
        <span>{newSessionMode === 'practice' ? '新练习' : '新对话'}</span>
        <kbd>⌘N</kbd>
      </button>
      <div className="search">
        <span>⌕</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="搜索会话内容、知识点"
          onKeyDown={(e) => e.key === 'Escape' && setQ('')}
        />
        {q && <button type="button" className="x" onClick={() => setQ('')} aria-label="清空">×</button>}
      </div>

      <div className="sessions">
        {searching ? (
          <>
            <div className="grp">
              {search.isFetching ? '搜索中…' : `${search.data?.hits.length ?? 0} 个结果`}
            </div>
            {search.data?.hits.length === 0 && !search.isFetching && (
              <SoftKitty compact variant="cushion" text={`没有包含「${debounced}」的会话`} />
            )}
            {search.data?.hits.map((h) => {
              const path = h.kind === 'teaching' ? `/teaching/${h.id}` : `/practice/${h.id}`;
              return (
                <button type="button" key={`${h.kind}-${h.id}`} className={`sess ${activeKey === path ? 'on' : ''}`} onClick={() => navigate(path)}>
                  <span className={`glyph ${h.kind === 'teaching' ? 't' : 'p'}`}>{h.kind === 'teaching' ? <IconAtom width={13} height={13} /> : <IconWhiteboard width={13} height={13} />}</span>
                  <span style={{ minWidth: 0 }}>
                    <span className="ttl">{h.title}</span>
                    <span className="meta snippet">{highlight(h.snippet, debounced)}</span>
                    <span className="meta">{h.status === 'active' ? '进行中' : '已结束'} · {shortTime(h.at)}</span>
                  </span>
                </button>
              );
            })}
          </>
        ) : (
          <>
            {groups.length === 0 && (
              <SoftKitty compact text={EMPTY.sessions} />
            )}
            {groups.map(([g, list]) => (
              <div key={g}>
                <div className="grp">{g}</div>
                {list.map((it) => {
                  const path = it.kind === 'teaching' ? `/teaching/${it.id}` : `/practice/${it.id}`;
                  const on = activeKey === path;
                  const live = it.kind === 'teaching' ? it.data.status === 'active' : !it.data.ended_at;
                  return (
                    <button type="button" key={`${it.kind}-${it.id}`} className={`sess ${on ? 'on' : ''}`} onClick={() => navigate(path)}>
                      <span className={`glyph ${it.kind === 'teaching' ? 't' : 'p'}`}>{it.kind === 'teaching' ? <IconAtom width={13} height={13} /> : <IconWhiteboard width={13} height={13} />}</span>
                      <span style={{ minWidth: 0 }}>
                        <span className="ttl">{titleOf(it, tree.data?.sectionById)}</span>
                        <span className="meta">{metaOf(it)}</span>
                      </span>
                      {live && <span className="live" />}
                    </button>
                  );
                })}
              </div>
            ))}
          </>
        )}
      </div>

      <div className="rail-bottom">
        <button type="button" className={`nav ${isReport ? 'on' : ''}`} onClick={() => navigate('/report')}>
          <span className="ico"><IconCouch /></span>
          <span className="nav-copy"><b>沙发周报</b><small>Couch log</small></span>
        </button>
        <button type="button" className={`nav ${isCards ? 'on' : ''}`} onClick={() => navigate('/cards')}>
          <span className="ico"><IconKey /></span>
          <span className="nav-copy"><b>公寓钥匙</b><small>Recognition cards</small></span>
        </button>
        <button type="button" className={`nav ${isSettings ? 'on' : ''}`} onClick={() => navigate('/settings')}>
          <span className="ico"><IconThermostat /></span>
          <span className="nav-copy"><b>室友协议</b><small>71°F · Settings</small></span>
        </button>
        <div className="me">
          <div className="avatar">{student?.name?.slice(0, 1) ?? '?'}</div>
          <div>
            <div className="nm">{student?.name}</div>
            <div className="sub">学号 #{student?.id}</div>
          </div>
          <button type="button" className="tutor" title="当前讲师 · 点击去换" onClick={() => navigate('/settings')}>
            <PersonaAvatar persona={student?.persona} size={26} />
            <span>{personaByKey(student?.persona).name}</span>
          </button>
        </div>
      </div>
    </aside>
  );
}

function highlight(text: string, kw: string) {
  if (!kw) return text;
  const idx = text.toLowerCase().indexOf(kw.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}<mark>{text.slice(idx, idx + kw.length)}</mark>{text.slice(idx + kw.length)}
    </>
  );
}

function titleOf(it: RailItem, sectionById?: Map<number, { title: string }>): string {
  if (it.kind === 'teaching') {
    if (it.data.source_practice_session_id) {
      const n = it.data.source_question_ids?.length ?? 0;
      return `来自练习 #${it.data.source_practice_session_id}${n > 1 ? ` · ${n} 题` : ''}`;
    }
    return it.data.preview || `会话 #${it.id}`;
  }
  const names = it.data.knowledge_point_ids
    .map((id) => sectionById?.get(id)?.title)
    .filter(Boolean) as string[];
  const scope = names.length ? names.slice(0, 2).join('、') + (names.length > 2 ? ' 等' : '') : '练习';
  return `${scope} · ${it.data.total_count} 题`;
}

function metaOf(it: RailItem) {
  if (it.kind === 'teaching') {
    const st = it.data.status === 'active' ? '进行中' : it.data.status === 'completed' ? '已结束' : '已取消';
    return (
      <>
        <span className="tag">{it.data.message_count} 条</span>· {st} · {shortTime(it.at)}
      </>
    );
  }
  const d = it.data;
  const done = d.correct_count + d.wrong_count + d.skip_count;
  const rate = d.correct_count + d.wrong_count > 0
    ? `${Math.round((d.correct_count / (d.correct_count + d.wrong_count)) * 100)}%`
    : '—';
  return (
    <>
      <span className="tag">{d.timed ? '计时' : '不计时'}</span>
      · {d.ended_at ? `正确率 ${rate}` : `${done} / ${d.total_count}`}
    </>
  );
}
