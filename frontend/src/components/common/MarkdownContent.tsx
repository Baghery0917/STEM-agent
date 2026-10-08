import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

interface Props {
  content: string;
  className?: string;
  /** 选项等行内场景：段落改成 span，避免按钮里套块级 p */
  inline?: boolean;
}

export default function MarkdownContent({ content, className, inline }: Props) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={inline ? { p: ({ children }) => <span>{children}</span> } : undefined}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
