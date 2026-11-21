import { Card, Empty, Typography } from "antd";

export default function DocumentsPage() {
    return (
        <>
            <Typography.Title level={3}>
                법률 자료
            </Typography.Title>

            <Card>
                <Empty
                    description="법률 문서 목록 조회 기능은 준비 중입니다."
                />
            </Card>
        </>
    );
}