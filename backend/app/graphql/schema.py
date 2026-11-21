import strawberry
from app.graphql.resolver import Query, Mutation


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)