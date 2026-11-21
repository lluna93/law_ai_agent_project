import { Card, Input, Button, Alert, Space } from "antd";
import { RobotOutlined } from "@ant-design/icons";

const { TextArea } = Input;

export default function ConsultForm({
                                        question,
                                        setQuestion,
                                        loading,
                                        onSubmit,
                                    }) {
    return (
        <Card title="법률 상담 내용 입력">
            <Space
                orientation="vertical"
                size="middle"
                style={{ width: "100%" }}
            >
                <Alert
                    type="warning"
                    showIcon
                    message="개인정보 입력 주의"
                    description="실명, 주민등록번호, 연락처 등 민감한 정보는 제외하고 상담 내용을 입력하세요."
                />

                <TextArea
                    rows={7}
                    maxLength={4000}
                    showCount
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="예: 임대차 계약이 종료되었는데 집주인이 보증금을 반환하지 않습니다."
                />

                <Button
                    type="primary"
                    icon={<RobotOutlined />}
                    loading={loading}
                    disabled={!question.trim()}
                    onClick={onSubmit}
                    size="large"
                    block
                >
                    AI 법률 상담하기
                </Button>
            </Space>
        </Card>
    );
}