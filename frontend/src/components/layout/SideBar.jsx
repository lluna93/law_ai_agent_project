import { Layout, Menu } from "antd";
import {
    RobotOutlined,
    HistoryOutlined,
    BookOutlined,
} from "@ant-design/icons";

import { useNavigate, useLocation } from "react-router-dom";

const { Sider } = Layout;

const items = [
    {
        key: "/agent",
        icon: <RobotOutlined />,
        label: "AI 법률 상담",
    },
    {
        key: "/history",
        icon: <HistoryOutlined />,
        label: "상담 내역",
    },
    {
        key: "/documents",
        icon: <BookOutlined />,
        label: "법률 자료",
    },
];

export default function SideBar() {
    const navigate = useNavigate();
    const location = useLocation();

    return (
        <Sider
            width={230}
            breakpoint="lg"
            collapsedWidth={0}
            theme="light"
            style={{
                minHeight: "calc(100vh - 64px)",
                borderRight: "1px solid #e5e7eb",
            }}
        >
            <Menu
                mode="inline"
                items={items}
                selectedKeys={[location.pathname]}
                onClick={({ key }) => navigate(key)}
                style={{
                    borderRight: 0,
                    paddingTop: 16,
                }}
            />
        </Sider>
    );
}