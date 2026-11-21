import { graphqlRequest } from "../client";

// 법률 상담 Mutation
const CONSULT_LAW = `
  mutation ConsultLaw($input: ConsultInput!) {
    consultLaw(input: $input) {
      answer
      status
      sources {
        source
        similarity
        content
      }
    }
  }
`;

// 법률 상담 API 호출
export async function consultLaw(question) {
    const data = await graphqlRequest(CONSULT_LAW, {
        input: {
            question,
        },
    });

    return data.consultLaw;
}