
import { graphqlRequest } from "../client";

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

const CONSULT_BOTH = `
  mutation ConsultBoth($input: ConsultInput!) {
    consultBoth(input: $input) {
      rag {
        answer
        status
        sources {
          source
          similarity
          content
        }
      }

      graphrag {
        answer
        status
        sources {
          source
          similarity
          content
          sourceType
          citedArticles
          concepts
          relatedCases
        }
      }
    }
  }
`;

export async function consultLaw(question) {
  const data = await graphqlRequest(
    CONSULT_LAW,
    { input: { question } }
  );

  return data.consultLaw;
}

export async function consultBoth(question) {
  const data = await graphqlRequest(
    CONSULT_BOTH,
    { input: { question } }
  );

  return data.consultBoth;
}
