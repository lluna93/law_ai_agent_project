
import { useMemo, useState } from "react";
import { Card, Button, Modal, Typography, Space, Alert, Empty } from "antd";
import {
    FileSearchOutlined,
    LinkOutlined,
} from "@ant-design/icons";

import { AgGridReact } from "ag-grid-react";
import {
    AllCommunityModule,
    ModuleRegistry,
    themeQuartz,
} from "ag-grid-community";

import styled from "styled-components";

// AG Grid v34 모듈 등록
ModuleRegistry.registerModules([AllCommunityModule]);

const { Text, Paragraph } = Typography;

// 국가법령정보센터 판례 검색 페이지
const CASE_SEARCH_URL = "https://www.law.go.kr/precSc.do";

// 원문 표시 영역
const ContentBox = styled.div`
  background: #f5f7fb;
  padding: 20px;
  border-radius: 8px;
  max-height: 450px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.9;
  border: 1px solid #e5e7eb;
`;

export default function SourceGrid({ sources = [] }) {
    // 선택한 법률 문서
    const [selectedSource, setSelectedSource] = useState(null);

    // AG Grid 데이터
    const rowData = useMemo(
        () =>
            sources.map((item, index) => ({
                ...item,
                rank: index + 1,
            })),
        [sources]
    );

    // AG Grid 컬럼
    const columnDefs = useMemo(
        () => [
            {
                headerName: "순위",
                field: "rank",
                width: 90,
            },
            {
                headerName: "법률 자료",
                field: "source",
                flex: 1,
                minWidth: 200,
            },
            {
                headerName: "유사도",
                field: "similarity",
                width: 130,
                valueFormatter: ({ value }) =>
                    value == null
                        ? "-"
                        : Number(value).toFixed(4),
            },
            {
                headerName: "상세보기",
                width: 140,
                sortable: false,
                filter: false,
                cellRenderer: (params) => (
                    <Button
                        type="link"
                        icon={<FileSearchOutlined />}
                        onClick={() => setSelectedSource(params.data)}
                    >
                        원문 보기
                    </Button>
                ),
            },
        ],
        []
    );

    // 판례 파일 여부 확인
    const isCaseDocument = selectedSource?.source?.includes("판례");

    return (
        <>
            <Card title="RAG 검색 출처 TOP 5">
                {rowData.length === 0 ? (
                    <Empty description="검색된 법률 자료가 없습니다." />
                ) : (
                    <div style={{ height: 330, width: "100%" }}>
                        <AgGridReact
                            theme={themeQuartz}
                            rowData={rowData}
                            columnDefs={columnDefs}
                            defaultColDef={{
                                sortable: true,
                                filter: true,
                                resizable: true,
                            }}
                            pagination
                            paginationPageSize={5}
                            onRowClicked={(event) =>
                                setSelectedSource(event.data)
                            }
                        />
                    </div>
                )}
            </Card>

            <Modal
                title="법률 자료 원문 보기"
                open={!!selectedSource}
                onCancel={() => setSelectedSource(null)}
                footer={null}
                width={850}
                destroyOnHidden
            >
                {selectedSource && (
                    <Space
                        orientation="vertical"
                        size="middle"
                        style={{ width: "100%" }}
                    >
                        <div>
                            <Text strong>출처: </Text>
                            <Text>{selectedSource.source}</Text>
                        </div>

                        <div>
                            <Text strong>검색 유사도: </Text>
                            <Text>
                                {Number(selectedSource.similarity).toFixed(4)}
                            </Text>
                        </div>

                        <Alert
                            type="info"
                            showIcon
                            message="RAG 검색 원문"
                            description="아래 내용은 PostgreSQL에 저장된 검색 청크입니다. 전체 법률 문서 또는 판결문과 다를 수 있습니다."
                        />

                        <ContentBox>
                            {selectedSource.content ||
                                "저장된 원문 내용이 없습니다."}
                        </ContentBox>

                        {isCaseDocument && (
                            <Button
                                icon={<LinkOutlined />}
                                onClick={() =>
                                    window.open(
                                        CASE_SEARCH_URL,
                                        "_blank",
                                        "noopener,noreferrer"
                                    )
                                }
                            >
                                국가법령정보센터에서 판례 검색
                            </Button>
                        )}

                        <Paragraph type="secondary">
                            실제 사건에 적용하기 전 공식 법령과 판례의
                            최신 내용을 확인하세요.
                        </Paragraph>
                    </Space>
                )}
            </Modal>
        </>
    );
}
