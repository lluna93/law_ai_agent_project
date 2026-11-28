import { useState } from "react";
import {
  Card,
  Tag,
  Typography,
  Button,
  Modal,
  Space,
  Divider,
  Empty,
} from "antd";

const { Paragraph, Text } = Typography;

function SourceList({
  sources = [],
  graph = false,
}) {
  const [selected, setSelected] = useState(null);

  return (
    <>
      {sources.length === 0 ? (
        <Empty description="검색 출처 없음" />
      ) : (
        sources.map((item, index) => (
          <div
            key={`${item.source}-${index}`}
            style={{
              padding: "9px 0",
              borderBottom: "1px solid #eee",
            }}
          >
            <Space wrap>
              <Text>
                {index + 1}. {item.source}
              </Text>

              <Tag>
                {Number(
                  item.similarity
                ).toFixed(4)}
              </Tag>

              <Button
                size="small"
                onClick={() =>
                  setSelected(item)
                }
              >
                원문 보기
              </Button>
            </Space>

            {graph && (
              <div style={{ marginTop: 5 }}>
                {(item.concepts || []).map(
                  (concept) => (
                    <Tag key={concept}>
                      {concept}
                    </Tag>
                  )
                )}
              </div>
            )}
          </div>
        ))
      )}

      <Modal
        title={
          selected?.source || "검색 원문"
        }
        open={!!selected}
        onCancel={() =>
          setSelected(null)
        }
        footer={null}
        width={800}
      >
        {selected && (
          <>
            <Paragraph
              style={{
                whiteSpace: "pre-wrap",
                maxHeight: 400,
                overflow: "auto",
                background: "#f6f7f9",
                padding: 16,
              }}
            >
              {selected.content ||
                "저장된 원문이 없습니다."}
            </Paragraph>

            {graph && (
              <Space orientation="vertical">
                <Text>
                  노드 유형:{" "}
                  {selected.sourceType}
                </Text>

                <Text>
                  참조 조문:{" "}
                  {(
                    selected.citedArticles || []
                  ).join(", ") || "없음"}
                </Text>

                <Text>
                  법률 개념:{" "}
                  {(
                    selected.concepts || []
                  ).join(", ") || "없음"}
                </Text>

                <Text>
                  관련 판례 ID:{" "}
                  {(
                    selected.relatedCases || []
                  ).join(", ") || "없음"}
                </Text>
              </Space>
            )}
          </>
        )}
      </Modal>
    </>
  );
}

export default function CompareAnswer({
  result,
}) {
  if (!result) return null;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns:
          "repeat(auto-fit, minmax(min(100%, 420px), 1fr))",
        gap: 16,
      }}
    >
      {[
        [
          "RAG · pgvector",
          result.rag,
          false,
        ],
        [
          "GraphRAG · Neo4j",
          result.graphrag,
          true,
        ],
      ].map(([title, data, graph]) => (
        <Card
          key={title}
          title={title}
          extra={
            <Tag
              color={
                data.status === "SUCCESS"
                  ? "green"
                  : "orange"
              }
            >
              {data.status}
            </Tag>
          }
        >
          <Paragraph
            style={{
              whiteSpace: "pre-wrap",
              lineHeight: 1.85,
            }}
          >
            {data.answer}
          </Paragraph>

          <Divider>
            검색 출처 TOP 5
          </Divider>

          <SourceList
            sources={data.sources}
            graph={graph}
          />
        </Card>
      ))}
    </div>
  );
}