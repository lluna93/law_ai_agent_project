import strawberry


@strawberry.input
class ConsultInput:
    question: str