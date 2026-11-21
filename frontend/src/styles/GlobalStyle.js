import { createGlobalStyle } from "styled-components";

// 프로젝트 전체에 적용할 공통 스타일
export const GlobalStyle = createGlobalStyle`
    * {
        box-sizing: border-box;
    }

    body {
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
        background: #f5f7fb;
        color: #243044;
    }

    #root {
        min-height: 100vh;
    }
`;