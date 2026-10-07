interface Props {
  practiceSessionId: number;
  content: string;
}

/**
 * 练习转教学的第一条消息：后端把题干、作答、答案拼成固定格式，
 * 这里把「（来自练习 #N）」头和各题块拆开渲染。
 */
export default function HandoffCard({ practiceSessionId, content }: Props) {
  const blocks = content.split(/\n\n+/).filter(Boolean);
  const header = blocks[0]?.startsWith('（来自练习') ? blocks.shift() : null;
  const questionBlocks = blocks.filter((b) => b.startsWith('【练习第'));
  const note = blocks.filter((b) => !b.startsWith('【练习第')).join('\n\n');
  const count = questionBlocks.length;
  return (
    <>
      <div className="handoff">
        <div className="hh">
          <span>练</span>
          {header ? header.replace(/[（）]/g, '') : `来自练习 #${practiceSessionId}`}
          <span className="sp">{count} 题</span>
        </div>
        <div className="hb">{questionBlocks.join('\n\n')}</div>
      </div>
      {note && <p>{note}</p>}
    </>
  );
}
