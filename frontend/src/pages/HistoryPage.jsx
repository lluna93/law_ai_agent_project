import { Card, Empty, Typography } from "antd";

export default function HistoryPage() {
    return (
        <>
            <Typography.Title level={3}>
                상담 내역
            </Typography.Title>

            <Card>
                <Empty
                    description="상담 내역 저장 기능은 준비 중입니다."
                />
            </Card>
        </>
    );
}