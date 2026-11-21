import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider } from "antd";

import App from "./App";
import { GlobalStyle } from "./styles/GlobalStyle";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <BrowserRouter>
            <ConfigProvider
                theme={{
                    token: {
                        colorPrimary: "#245da0",
                        borderRadius: 8,
                    },
                }}
            >
                <GlobalStyle />
                <App />
            </ConfigProvider>
        </BrowserRouter>
    </React.StrictMode>
);