import { useEffect, useState } from "react";
import { Layout } from "antd";
import { Outlet } from "react-router-dom";

import HeaderBar from "./HeaderBar";
import SideBar from "./SideBar";
import { checkHealth } from "../../graphql/query/health";

const { Content } = Layout;

export default function MainLayout() {
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        // 최초 진입 시 GraphQL 연결 확인
        checkHealth()
            .then(() => setConnected(true))
            .catch(() => setConnected(false));
    }, []);

    return (
        <Layout style={{ minHeight: "100vh" }}>
            <HeaderBar connected={connected} />

            <Layout>
                <SideBar />

                <Content style={{ padding: 28, minWidth: 0 }}>
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}