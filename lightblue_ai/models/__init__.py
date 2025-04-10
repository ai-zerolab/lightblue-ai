from pydantic_ai.models import Model
from pydantic_ai.models import infer_model as legacy_infer_model

from lightblue_ai.models.anthropic import AnthropicModel as PatchedAnthropicModel
from lightblue_ai.models.bedrock import (
    BedrockConverseModel as PatchedBedrockConverseModel,
)


def infer_model(model: str | Model):
    if not isinstance(model, str):
        return legacy_infer_model(model)

    if model.startswith("bedrock:"):
        return PatchedBedrockConverseModel(model.lstrip("bedrock:"))

    if model.startswith("anthropic:"):
        return PatchedAnthropicModel(model.lstrip("anthropic:"))

    return legacy_infer_model(model)
