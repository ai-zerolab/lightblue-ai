from typing import Annotated, Any

import httpx
from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class HTTPRequestTool(LightBlueTool):
    def __init__(self):
        self.name = "http_request_tool"
        self.scopes = [Scope.web]
        self.description = "Makes an HTTP request to a URL and get the response."
        self.client = httpx.AsyncClient()

    async def call(
        self,
        url: Annotated[str, Field(description="URL to make the request to")],
        method: Annotated[str, Field(description="HTTP method")],
        headers: Annotated[dict[str, Any] | None, Field(description="Request headers")] = None,
        data: Annotated[dict[str, Any] | None, Field(description="Request data")] = None,
        authrization: Annotated[
            str | None,
            Field(
                description="Authorization header to use for the request. If not provided, the tool will not include an authorization header. e.g. Bearer <token>"
            ),
        ] = None,
    ) -> dict[str, Any] | str:
        headers = headers or {}
        if authrization:
            headers["Authorization"] = authrization
        response = await self.client.request(method, url, headers=headers, json=data)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return {"error": str(e), "status_code": e.response.status_code, "response": e.response.text}
        else:
            return response.json() if response.headers["Content-Type"] == "application/json" else response.text


@hookimpl
def register(manager):
    manager.register(HTTPRequestTool())
