import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { startPractice } from '@/api/practice';
import { getStudentReport } from '@/api/reports';
import { useStudentStore } from '@/stores/studentStore';
import { toast } from '@/stores/toastStore';
import { usePracticeSessions } from '@/hooks/useSessionLists';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import TopBar from '@/components/shell/TopBar';
import SetupPanel from '@/components/practice/SetupPanel';
import { shortTime } from '@/utils/time';

export default function PracticeSetup() {
  const student = useStudentStore((s) => s.current)!;
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();
  const preselect = (location.state as { preselect?: number[] } | null)?.preselect;
  const tree = useKnowledgeTree();
  const recent = usePracticeSessions(student.id);
  const report = useQuery({
    queryKey: ['student-report', student.id, 'all', 'nosummary'],
    queryFn: () => getStudentReport(student.id, 'all', false),
    staleTime: 60_000,
  });

  const suggested = [...(report.data?.knowledge_points ?? [])]
    .sort((a, b) => a.mastery_level - b.mastery_level)
    .slice(0, 4)
    .map((k) => ({ section_id: k.section_id, title: k.section_title, mastery: k.mastery_level }));

  const start = useMutation({
    mutationFn: startPractice,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['practice-sessions', student.id] });
      navigate(`/practice/${data.session.id}`, { state: data });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const recentList = (recent.data ?? []).slice(0, 3);

  return (
    <>
      <TopBar crumb="新练习" />
      <section className="stage">
        <div className="psetup">
          <div className="left">
            <div className="kicker">Whiteboard session</div>
            <h1 className="hi">开始一次练习</h1>
            <p>在右边设置范围和参数，确认后开始出题。做题途中任何一题都可以跳过；不计时时任何一题都可以一键转到教学模式追问。</p>
            {recentList.length > 0 && (
              <>
                <div className="grp" style={{ paddingLeft: 0 }}>最近的练习</div>
                <div className="recent col1">
                  {recentList.map((s) => {
                    const names = s.knowledge_point_ids.map((id) => tree.data?.sectionById.get(id)?.title).filter(Boolean) as string[];
                    const answered = s.correct_count + s.wrong_count;
                    const rate = answered ? `正确率 ${Math.round((s.correct_count / answered) * 100)}%` : '未作答';
                    return (
                      <button type="button" key={s.id} className="rc" onClick={() => navigate(`/practice/${s.id}`)}>
                        <b>{names.slice(0, 2).join('、') || '练习'} · {s.total_count} 题</b>
                        <span className="m">{shortTime(s.started_at)} · {s.timed ? '计时' : '不计时'} · {s.ended_at ? rate : '进行中'}</span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
            <img className="art" src={`${import.meta.env.BASE_URL}tbbt/backgrounds/four-heads-cream.jpg`} alt="" draggable={false} />
          </div>
          <div className="right">
            <SetupPanel
              inline
              studentId={student.id}
              suggested={suggested}
              preselect={preselect}
              loading={start.isPending}
              onStart={(body) => start.mutate(body)}
            />
          </div>
        </div>
      </section>
    </>
  );
}
