from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel


def to_iso8601_utc(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcDateTime = Annotated[
    datetime,
    PlainSerializer(to_iso8601_utc, return_type=str, when_used="json"),
]


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )
