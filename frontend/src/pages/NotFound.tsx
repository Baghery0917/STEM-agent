import { useNavigate } from 'react-router-dom';
import { NOT_FOUND } from '@/theme/copy';

/** 404：薛定谔的猫箱 */
export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="agent">
      <div className="notfound">
        <div className="box" aria-hidden="true">
          <span className="lid" /><span className="q">?</span>
        </div>
        <h1>{NOT_FOUND.title}</h1>
        <p>{NOT_FOUND.body}</p>
        <button type="button" className="btn pri" onClick={() => navigate('/teaching', { replace: true })}>回到教学页</button>
      </div>
    </div>
  );
}
