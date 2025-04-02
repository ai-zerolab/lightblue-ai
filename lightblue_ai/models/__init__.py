from pydantic_ai.models import infer_model as legacy_infer_model

from lightblue_ai.models.bedrock import BedrockConverseModel as PatchedBedrockConverseModel


def infer_model(model: str):
    if "bedrock:" in model:
        return PatchedBedrockConverseModel(model.lstrip("bedrock:"))
    return legacy_infer_model(model)
