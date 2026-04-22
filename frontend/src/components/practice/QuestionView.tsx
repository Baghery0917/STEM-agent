import { Checkbox, Input, Radio, Space, Typography } from 'antd';
import type { QuestionResponse } from '@/api/types';

interface Props {
  question: QuestionResponse;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

function parseChoices(content: string): { prefix: string; label: string }[] {
  const lines = content.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const choiceLines = lines.filter((l) => /^[A-Z][\.．、:：\s]/.test(l));
  if (choiceLines.length < 2) return [];
  return choiceLines.map((line) => {
    const prefix = line.charAt(0);
    const label = line.slice(1).replace(/^[\.．、:：\s]+/, '').trim();
    return { prefix, label };
  });
}

function parseQuestionBody(content: string): string {
  const lines = content.split(/\n+/);
  const body: string[] = [];
  for (const line of lines) {
    if (/^[A-Z][\.．、:：\s]/.test(line.trim())) break;
    body.push(line);
  }
  return body.join('\n');
}

export default function QuestionView({ question, value, onChange, disabled }: Props) {
  const choices = parseChoices(question.content);
  const body = parseQuestionBody(question.content);

  const renderAnswerInput = () => {
    if (question.type === 'single_choice' && choices.length >= 2) {
      return (
        <Radio.Group
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
        >
          {choices.map((c) => (
            <Radio key={c.prefix} value={c.prefix} style={{ padding: '6px 0' }}>
              <strong style={{ marginRight: 8 }}>{c.prefix}.</strong>
              {c.label}
            </Radio>
          ))}
        </Radio.Group>
      );
    }

    if (question.type === 'multiple_choice' && choices.length >= 2) {
      const selected = value ? value.split('').filter((ch) => /[A-Z]/.test(ch)) : [];
      return (
        <Checkbox.Group
          value={selected}
          onChange={(vals) => onChange((vals as string[]).sort().join(''))}
          disabled={disabled}
          style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
        >
          {choices.map((c) => (
            <Checkbox key={c.prefix} value={c.prefix} style={{ padding: '6px 0' }}>
              <strong style={{ marginRight: 8 }}>{c.prefix}.</strong>
              {c.label}
            </Checkbox>
          ))}
        </Checkbox.Group>
      );
    }

    if (question.type === 'fill_blank') {
      return (
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder="请填入答案"
        />
      );
    }

    return (
      <Input.TextArea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="请写下你的答案或解题过程"
        autoSize={{ minRows: 4, maxRows: 12 }}
      />
    );
  };

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Typography.Paragraph
        style={{ fontSize: 16, whiteSpace: 'pre-wrap', marginBottom: 0 }}
      >
        {body || question.content}
      </Typography.Paragraph>
      {question.content_image && (
        <img
          src={question.content_image}
          alt="题目图片"
          style={{ maxWidth: '100%', borderRadius: 6, border: '1px solid #f0f0f0' }}
        />
      )}
      <div>{renderAnswerInput()}</div>
    </Space>
  );
}
