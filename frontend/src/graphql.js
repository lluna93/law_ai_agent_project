// 프론트에서 필요한 응답 필드를 직접 지정
export const CONSULT_LAW = `
  mutation ConsultLaw($input: ConsultInput!) {
    consultLaw(input: $input) {
      answer
      status
      sources {
        source
        similarity
      }
    }
  }
`;