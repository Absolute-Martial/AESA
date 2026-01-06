"""GraphQL types for assistant settings."""

from typing import Optional

import strawberry


@strawberry.type(description="Assistant runtime settings")
class AssistantSettings:
    base_url: Optional[str] = None
    model: Optional[str] = None


@strawberry.input(description="Update assistant runtime settings")
class UpdateAssistantSettingsInput:
    base_url: Optional[str] = None
    model: Optional[str] = None
