"""GraphQL schema configuration for AESA."""

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.graphql.resolvers import Query, Mutation
from app.core.config import get_settings


def create_graphql_schema() -> strawberry.Schema:
    """Create the Strawberry GraphQL schema."""
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
    )


def create_graphql_router() -> GraphQLRouter:
    """
    Create the GraphQL router for FastAPI integration.

    Enables GraphiQL in development mode for API exploration.
    """
    settings = get_settings()
    schema = create_graphql_schema()

    return GraphQLRouter(
        schema,
        graphiql=settings.debug,  # Enable GraphiQL in debug mode
        path="/graphql",
    )


# Create schema instance for direct access
schema = create_graphql_schema()
