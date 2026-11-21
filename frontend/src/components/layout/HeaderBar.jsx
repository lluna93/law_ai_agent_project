import { Layout, Typography, Space, Tag } from "antd";
import { ReadOutlined } from "@ant-design/icons";
import styled from "styled-components";

const Header = styled(Layout.Header)`
    height: 64px;
    padding: 0 24px;
    background: #172b4d;
    display: flex;
    align-items: center;
    justify-content: space-between;
`;

export default function HeaderBar({ connected }) {
    return (
        <Header>
            <Space>
                <ReadOutlined
                    style={{ color: "white", fontSize: 22 }}
                />

                <Typography.Text
                    strong
                    style={{ color: "white", fontSize: 18 }}
                >
                    Law AI Agent
                </Typography.Text>
            </Space>

            <Tag color={connected ? "success" : "error"}>
                {connected ? "GraphQL 연결" : "서버 연결 안 됨"}
            </Tag>
        </Header>
    );
}