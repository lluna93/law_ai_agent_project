import { useState } from "react";
import {
  Alert,
  Button,
  Card,
  Input,
  Space,
  Typography,
} from "antd";

import { consultBoth } from "../graphql/query/agent";
import CompareAnswer from "../components/agent/CompareAnswer";

const { Title, Paragraph } = Typography;

export default function AgentPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleConsult = async () => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      setResult(
        await consultBoth(question.trim())
      );
    } catch (err) {
      console.error(err);
      setError(
        err.message || "상담 요청 오류"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 1440,
        margin: "0 auto",
      }}
    >
      <Title level={3}>
        AI 법률 상담 · RAG vs GraphRAG
      </Title>

      <Paragraph type="secondary">
        동일한 질문에 대해 문서 유사도 검색과
        그래프 관계 검색 결과를 비교합니다.
      </Paragraph>

      <Space
        orientation="vertical"
        size="large"
        style={{ width: "100%" }}
      >
        <Card>
          <Input.TextArea
            rows={5}
            maxLength={2000}
            showCount
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            placeholder="법률 상담 질문을 입력하세요."
          />

          <Button
            type="primary"
            loading={loading}
            onClick={handleConsult}
            style={{ marginTop: 18 }}
          >
            RAG + GraphRAG 비교 상담
          </Button>
        </Card>

        {error && (
          <Alert
            type="error"
            showIcon
            message="상담 요청 오류"
            description={error}
          />
        )}

        <CompareAnswer result={result} />
      </Space>
    </div>
  );
}