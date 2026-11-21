import { graphqlRequest } from "../client";

// 백엔드 Query.health와 연결
const HEALTH_QUERY = `
  query {
    health
  }
`;

export async function checkHealth() {
    const data = await graphqlRequest(HEALTH_QUERY);

    return data.health;
}