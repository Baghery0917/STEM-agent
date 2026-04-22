import { App, Button, Input, Modal, Typography, Upload } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { bulkImportKnowledge, type BulkImportResult } from '@/api/knowledge';

const { Dragger } = Upload;

interface Props {
  open: boolean;
  onClose: () => void;
}

const SAMPLE = JSON.stringify(
  {
    volumes: [
      {
        name: '力学',
        chapters: [
          {
            name: '运动学',
            sections: [{ name: '匀变速直线运动', description: '...' }],
          },
        ],
      },
    ],
  },
  null,
  2,
);

export default function BulkImportModal({ open, onClose }: Props) {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [text, setText] = useState(SAMPLE);
  const [result, setResult] = useState<BulkImportResult | null>(null);

  const mutation = useMutation({
    mutationFn: bulkImportKnowledge,
    onSuccess: (res) => {
      setResult(res);
      queryClient.invalidateQueries({ queryKey: ['knowledge-tree'] });
      if (res.errors.length === 0) {
        message.success('全部导入成功');
      } else {
        message.warning(`完成，但有 ${res.errors.length} 条错误`);
      }
    },
    onError: (err: Error) => message.error(err.message),
  });

  const handleImport = () => {
    try {
      const parsed = JSON.parse(text);
      if (!parsed.volumes || !Array.isArray(parsed.volumes)) {
        throw new Error('JSON 格式错误：缺少 volumes 数组');
      }
      setResult(null);
      mutation.mutate(parsed);
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  const uploadProps: UploadProps = {
    accept: '.json',
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = () => setText(String(reader.result));
      reader.readAsText(file);
      return false;
    },
    showUploadList: false,
  };

  return (
    <Modal
      open={open}
      title="批量导入知识结构"
      width={720}
      onCancel={() => {
        setResult(null);
        onClose();
      }}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button key="import" type="primary" loading={mutation.isPending} onClick={handleImport}>
          开始导入
        </Button>,
      ]}
    >
      <Typography.Paragraph type="secondary">
        粘贴或上传 JSON，格式示例见文本框。当前后端无批量导入端点，前端将按顺序调用创建 API。
      </Typography.Paragraph>
      <Dragger {...uploadProps} style={{ marginBottom: 12 }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p>点击或拖拽 JSON 文件到此区域</p>
      </Dragger>
      <Input.TextArea
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoSize={{ minRows: 8, maxRows: 20 }}
        style={{ fontFamily: 'monospace' }}
      />
      {result && (
        <div style={{ marginTop: 16 }}>
          <Typography.Paragraph>
            ✅ 创建册 {result.volumesCreated}、章 {result.chaptersCreated}、节 {result.sectionsCreated}；
            错误 {result.errors.length}
          </Typography.Paragraph>
          {result.errors.length > 0 && (
            <pre
              style={{
                background: '#fff1f0',
                padding: 12,
                borderRadius: 6,
                maxHeight: 200,
                overflow: 'auto',
              }}
            >
              {result.errors.map((e) => `${e.path}: ${e.message}`).join('\n')}
            </pre>
          )}
        </div>
      )}
    </Modal>
  );
}
