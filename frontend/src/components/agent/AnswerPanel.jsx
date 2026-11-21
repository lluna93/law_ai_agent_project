import { Card, Alert, Tag, Typography } from "antd";
import styled from "styled-components";

const Answer = styled.div`
  white-space: pre-wrap;
  line-height: 1.9;
  padding: 18px;
  background: #f8fafc;
  border-radius: 8px;
  margin: 16px 0;
`;

export default function AnswerPanel({ result }) {
    if (!result) return null;

    const success = result.status === "SUCCESS";

    return (
        <Card
            title="AI 법률 상담 결과"
            extra={
                <Tag color={success ? "success" : "warning"}>
                    {result.status}
                </Tag>
            }
        >
            <Answer>{result.answer}</Answer>

            <Alert
                type="info"
                showIcon
                message="법률 정보 이용 안내"
                description="AI 답변은 일반적인 법률 정보이며 변호사의 법률 자문을 대체하지 않습니다. 현행 법령과 실제 적용 여부를 확인하세요."
            />
        </Card>
    );
}