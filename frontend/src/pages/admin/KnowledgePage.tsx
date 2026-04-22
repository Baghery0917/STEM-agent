import { Button, Card, Col, Row, Space, Spin, Tree, Typography } from 'antd';
import type { DataNode } from 'antd/es/tree';
import { PlusOutlined, UploadOutlined } from '@ant-design/icons';
import { useMemo, useState } from 'react';
import { useKnowledgeTree } from '@/hooks/useKnowledgeTree';
import NodeEditForm, { type SelectedNode } from '@/components/knowledge/NodeEditForm';
import BulkImportModal from '@/components/knowledge/BulkImportModal';
import type {
  ChapterResponse,
  SectionResponse,
  VolumeResponse,
} from '@/api/types';

export default function KnowledgePage() {
  const tree = useKnowledgeTree();
  const [selected, setSelected] = useState<SelectedNode | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const treeData = useMemo<DataNode[]>(() => {
    if (!tree.data) return [];
    return tree.data.volumes.map((v) => ({
      key: `v-${v.id}`,
      title: v.title,
      children: (tree.data!.byVolume.get(v.id) ?? []).map((c) => ({
        key: `c-${c.id}`,
        title: c.title,
        children: (tree.data!.byChapter.get(c.id) ?? []).map((s) => ({
          key: `s-${s.id}`,
          title: s.title,
          isLeaf: true,
        })),
      })),
    }));
  }, [tree.data]);

  const handleSelect = (keys: React.Key[]) => {
    const key = keys[0] as string | undefined;
    if (!key || !tree.data) return setSelected(null);
    const [prefix, idStr] = key.split('-');
    const id = Number(idStr);
    if (prefix === 'v') {
      const node = tree.data.volumeById.get(id) ?? null;
      setSelected({ kind: 'volume', node });
    } else if (prefix === 'c') {
      const node = tree.data.chapterById.get(id) ?? null;
      setSelected({ kind: 'chapter', node, parentId: node?.volume_id });
    } else {
      const node = tree.data.sectionById.get(id) ?? null;
      setSelected({ kind: 'section', node, parentId: node?.chapter_id });
    }
  };

  const newNode = (kind: 'volume' | 'chapter' | 'section', parentId?: number) => {
    const base = { id: -1, title: '', description: '', order: 0, created_at: null, updated_at: null };
    if (kind === 'volume') {
      setSelected({ kind, node: { ...base } as VolumeResponse });
    } else if (kind === 'chapter') {
      setSelected({
        kind,
        node: { ...base, volume_id: parentId! } as ChapterResponse,
        parentId,
      });
    } else {
      setSelected({
        kind,
        node: { ...base, chapter_id: parentId!, content: '' } as SectionResponse,
        parentId,
      });
    }
  };

  return (
    <>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          知识结构管理
        </Typography.Title>
        <Space>
          <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
            批量 JSON 导入
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => newNode('volume')}>
            新建册
          </Button>
        </Space>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={12} lg={10}>
          <Card title="知识树" bodyStyle={{ minHeight: 480 }}>
            {tree.isLoading ? (
              <div style={{ textAlign: 'center', padding: 24 }}>
                <Spin />
              </div>
            ) : treeData.length === 0 ? (
              <Typography.Paragraph type="secondary">
                暂无知识结构，点击右上方 "新建册" 或 "批量 JSON 导入"。
              </Typography.Paragraph>
            ) : (
              <Tree
                treeData={treeData}
                onSelect={handleSelect}
                defaultExpandAll
                titleRender={(node) => {
                  const key = String(node.key);
                  const [prefix, idStr] = key.split('-');
                  return (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <span>{node.title as string}</span>
                      {prefix !== 's' && (
                        <Button
                          size="small"
                          type="link"
                          icon={<PlusOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (prefix === 'v') newNode('chapter', Number(idStr));
                            else newNode('section', Number(idStr));
                          }}
                        />
                      )}
                    </span>
                  );
                }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} md={12} lg={14}>
          <Card title="节点详情" bodyStyle={{ minHeight: 480 }}>
            <NodeEditForm selected={selected} />
          </Card>
        </Col>
      </Row>

      <BulkImportModal open={importOpen} onClose={() => setImportOpen(false)} />
    </>
  );
}
