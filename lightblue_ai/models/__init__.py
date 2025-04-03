from pydantic_ai.models import Model
from pydantic_ai.models import infer_model as legacy_infer_model

from lightblue_ai.models.bedrock import (
    BedrockConverseModel as PatchedBedrockConverseModel,
)


def infer_model(model: str | Model):
    if not isinstance(model, str):
        return legacy_infer_model(model)

    if "bedrock:" in model:
        return PatchedBedrockConverseModel(model.lstrip("bedrock:"))
    return legacy_infer_model(model)
