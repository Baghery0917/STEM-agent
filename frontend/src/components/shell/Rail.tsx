import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useStudentStore } from '@/stores/studentStore';
import { useUiStore } from '@/stores/uiStore';
import { useRailItems, type RailItem } from '@/hooks/useSessionLists';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import { groupLabel, shortTime } from '@/utils/time';

const GROUP_ORDER = ['今天', '昨天', '过去 7 天', '更早'] as const;

export default function Rail() {
  const student = useStudentStore((s) => s.current);
  const mode = useUiStore((s) => s.mode);
  const navigate = useNavigate();
  const location = useLocation();
  const { items } = useRailItems(student?.id);
  const tree = useKnowledgeTree();
  const [q, setQ] = useState('');

  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase();
    if (!kw) return items;
    return items.filter((it) => titleOf(it, tree.data?.sectionById).toLowerCase().includes(kw));
  }, [items, q, tree.data]);

  const groups = useMemo(() => {
    const map = new Map<string, RailItem[]>();
    for (const it of filtered) {
      const g = groupLabel(it.at);
      map.set(g, [...(map.get(g) ?? []), it]);
    }
    return GROUP_ORDER.filter((g) => map.has(g)).map((g) => [g, map.get(g)!] as const);
  }, [filtered]);

  const activeKey = location.pathname;
  const isReport = activeKey.startsWith('/report');
  const isSettings = activeKey.startsWith('/settings');

  const newSession = () => navigate(mode === 'practice' ? '/practice/new' : '/teaching');

  return (
    <aside className="rail">
      <div className="brand">
        <div className="logo">S</div>
        <b>STEM Agent</b>
        <span className="ver">{student?.name ?? ''}</span>
      </div>
      <button type="button" className="new-btn" onClick={newSession}>
        <span>＋</span>
        <span>{mode === 'practice' ? '新练习' : '新对话'}</span>
        <kbd>⌘N</kbd>
      </button>
      <div className="search">
        <span>⌕</span>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="搜索会话" />
      </div>

      <div className="sessions">
        {groups.length === 0 && (
          <div className="sess-empty">{q ? '没有匹配的会话' : '还没有会话，先发一道题或开始练习'}</div>
        )}
        {groups.map(([g, list]) => (
          <div key={g}>
            <div className="grp">{g}</div>
            {list.map((it) => {
              const path = it.kind === 'teaching' ? `/teaching/${it.id}` : `/practice/${it.id}`;
              const on = activeKey === path;
              const live =
                it.kind === 'teaching' ? it.data.status === 'active' : !it.data.ended_at;
              return (
                <button
                  type="button"
                  key={`${it.kind}-${it.id}`}
                  className={`sess ${on ? 'on' : ''}`}
                  onClick={() => navigate(path)}
                >
                  <span className={`glyph ${it.kind === 'teaching' ? 't' : 'p'}`}>
                    {it.kind === 'teaching' ? '讲' : '练'}
                  </span>
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
      </div>

      <div className="rail-bottom">
        <button type="button" className={`nav ${isReport ? 'on' : ''}`} onClick={() => navigate('/report')}>
          <span className="ico">◔</span> 学习报告
        </button>
        <button type="button" className={`nav ${isSettings ? 'on' : ''}`} onClick={() => navigate('/settings')}>
          <span className="ico">⚙</span> 设置
        </button>
        <div className="me">
          <div className="avatar">{student?.name?.slice(0, 1) ?? '?'}</div>
          <div>
            <div className="nm">{student?.name}</div>
            <div className="sub">学号 #{student?.id}</div>
          </div>
        </div>
      </div>
    </aside>
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
      · {d.ended_at ? `正确率 ${rate}` : `${done} / ${d.total_count} · 对 ${d.correct_count}`}
    </>
  );
}
