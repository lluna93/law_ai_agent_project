
// Nginx가 /graphql 요청을 FastAPI로 전달
// 개발 환경에서는 Vite proxy 설정을 사용

const GRAPHQL_URL = "/graphql";

export async function graphqlRequest(query, variables = {}) {
    const response = await fetch(GRAPHQL_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            query,
            variables,
        }),
    });

    if (!response.ok) {
        throw new Error(
            `GraphQL HTTP 오류: ${response.status}`
        );
    }

    const result = await response.json();

    if (result.errors?.length) {
        throw new Error(
            result.errors.map((error) => error.message).join("\n")
        );
    }

    return result.data;
}
