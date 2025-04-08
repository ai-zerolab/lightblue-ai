import pydantic


class StreamEvent(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow", from_attributes=True)
