import { useState } from "react";
import { Typography, Space, Alert } from "antd";

import { consultLaw } from "../graphql/query/agent";

import ConsultForm from "../components/agent/ConsultForm";
import AnswerPanel from "../components/agent/AnswerPanel";
import SourceGrid from "../components/agent/SourceGrid";

const { Title, Paragraph } = Typography;

export default function AgentPage() {
    const [question, setQuestion] = useState("");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // GraphQL을 통한 AI 법률 상담
    const handleConsult = async () => {
        if (!question.trim() || loading) return;

        setLoading(true);
        setError("");
        setResult(null);

        try {
            const data = await consultLaw(question.trim());

            // RAG 검색 결과 확인
            console.log("GraphQL 상담 응답:", data);
            console.log("검색 출처:", data.sources);

            setResult(data);
        } catch (err) {
            console.error("법률 상담 오류:", err);
            setError(err.message || "상담 요청에 실패했습니다.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
            <Title level={3}>AI 법률 상담</Title>

            <Paragraph type="secondary">
                관련 법률 및 판례를 RAG로 검색하고
                LLM을 통해 법률 정보를 안내합니다.
            </Paragraph>

            <Space
                orientation="vertical"
                size="large"
                style={{ width: "100%" }}
            >
                <ConsultForm
                    question={question}
                    setQuestion={setQuestion}
                    loading={loading}
                    onSubmit={handleConsult}
                />

                {error && (
                    <Alert
                        type="error"
                        showIcon
                        message="상담 요청 오류"
                        description={error}
                    />
                )}

                {result && (
                    <>
                        <AnswerPanel result={result} />

                        <SourceGrid sources={result.sources ?? []} />
                    </>
                )}
            </Space>
        </div>
    );
}