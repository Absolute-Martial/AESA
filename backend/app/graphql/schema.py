"""GraphQL schema configuration for AESA."""

from __future__ import annotations

import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter

from app.core.config import get_settings
from app.core.database import async_session_maker, get_db
from app.graphql.resolvers import Mutation, Query
from app.models import User


async def _close_db_session(response, context):
    db = (context or {}).get("db")
    if db is not None:
        await db.close()


def create_graphql_schema() -> strawberry.Schema:
    """Create the Strawberry GraphQL schema."""
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
    )


async def _get_or_create_default_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(email="dev@example.com", name="Development User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _context_getter(request: Request):
    db: AsyncSession | None = getattr(getattr(request, "state", None), "db", None)
    if db is None:
        # Covers `schema.execute(...)` in property tests where there's no ASGI request lifecycle.
        db = async_session_maker()

    try:
        user = await _get_or_create_default_user(db)
        return {"request": request, "db": db, "user": user}
    finally:
        if getattr(getattr(request, "state", None), "db", None) is None:
            await db.close()


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
        context_getter=_context_getter,
    )


# Create schema instance for direct access
schema = create_graphql_schema()
