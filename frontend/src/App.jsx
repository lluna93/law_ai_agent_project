import { Routes, Route, Navigate } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import AgentPage from "./pages/AgentPage";
import HistoryPage from "./pages/HistoryPage";
import DocumentsPage from "./pages/DocumentsPage";

export default function App() {
    return (
        <Routes>
            <Route element={<MainLayout />}>
                <Route
                    path="/"
                    element={<Navigate to="/agent" replace />}
                />

                <Route path="/agent" element={<AgentPage />} />

                <Route path="/history" element={<HistoryPage />} />

                <Route path="/documents" element={<DocumentsPage />} />
            </Route>
        </Routes>
    );
}