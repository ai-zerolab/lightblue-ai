import asyncio
import io
import os
from pathlib import Path
from typing import Annotated, Any

import httpx
from PIL import Image
from pydantic import Field
from pydantic_ai import Tool

from lightblue.log import logger
from lightblue.settings import Settings
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl

API_URL = "https://api.bfl.ml"
API_ENDPOINTS = {
    "flux.1-pro": "flux-pro",
    "flux.1-dev": "flux-dev",
    "flux.1.1-pro": "flux-pro-1.1",
}


class ApiException(Exception):
    def __init__(self, status_code: int, detail: str | list[dict] | None = None):
        super().__init__()
        self.detail = detail
        self.status_code = status_code

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        if self.detail is None:
            message = None
        elif isinstance(self.detail, str):
            message = self.detail
        else:
            message = "[" + ",".join(d["msg"] for d in self.detail) + "]"
        return f"ApiException({self.status_code=}, {message=}, detail={self.detail})"


class ImageRequest:
    def __init__(  # noqa: C901
        self,
        # api inputs
        prompt: str,
        name: str = "flux.1.1-pro",
        width: int | None = None,
        height: int | None = None,
        num_steps: int | None = None,
        prompt_upsampling: bool | None = None,
        seed: int | None = None,
        guidance: float | None = None,
        interval: float | None = None,
        safety_tolerance: int | None = None,
        # behavior of this class
        validate: bool = True,
        api_key: str | None = None,
    ):
        """
        Manages an image generation request to the API.

        All parameters not specified will use the API defaults.

        Args:
            prompt: Text prompt for image generation.
            width: Width of the generated image in pixels. Must be a multiple of 32.
            height: Height of the generated image in pixels. Must be a multiple of 32.
            name: Which model version to use
            num_steps: Number of steps for the image generation process.
            prompt_upsampling: Whether to perform upsampling on the prompt.
            seed: Optional seed for reproducibility.
            guidance: Guidance scale for image generation.
            safety_tolerance: Tolerance level for input and output moderation.
                 Between 0 and 6, 0 being most strict, 6 being least strict.
            validate: Run input validation
            api_key: Your API key if not provided by the environment

        Raises:
            ValueError: For invalid input, when `validate`
            ApiException: For errors raised from the API
        """
        if validate:
            if name not in API_ENDPOINTS:
                raise ValueError(f"Invalid model {name}")
            elif width is not None and width % 32 != 0:
                raise ValueError(f"width must be divisible by 32, got {width}")
            elif width is not None and not (256 <= width <= 1440):
                raise ValueError(f"width must be between 256 and 1440, got {width}")
            elif height is not None and height % 32 != 0:
                raise ValueError(f"height must be divisible by 32, got {height}")
            elif height is not None and not (256 <= height <= 1440):
                raise ValueError(f"height must be between 256 and 1440, got {height}")
            elif num_steps is not None and not (1 <= num_steps <= 50):
                raise ValueError(f"steps must be between 1 and 50, got {num_steps}")
            elif guidance is not None and not (1.5 <= guidance <= 5.0):
                raise ValueError(f"guidance must be between 1.5 and 4, got {guidance}")
            elif interval is not None and not (1.0 <= interval <= 4.0):
                raise ValueError(f"interval must be between 1 and 4, got {interval}")
            elif safety_tolerance is not None and not (0 <= safety_tolerance <= 6.0):
                raise ValueError(f"safety_tolerance must be between 0 and 6, got {interval}")

            if name == "flux.1-dev":  # noqa: SIM102
                if interval is not None:
                    raise ValueError("Interval is not supported for flux.1-dev")
            if name == "flux.1.1-pro":  # noqa: SIM102
                if interval is not None or num_steps is not None or guidance is not None:
                    raise ValueError("Interval, num_steps and guidance are not supported for flux.1.1-pro")

        self.name = name
        self.request_json = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": num_steps,
            "prompt_upsampling": prompt_upsampling,
            "seed": seed,
            "guidance": guidance,
            "interval": interval,
            "safety_tolerance": safety_tolerance,
        }
        self.request_json = {key: value for key, value in self.request_json.items() if value is not None}

        self.request_id: str | None = None
        self.result: dict | None = None
        self._image_bytes: bytes | None = None
        self._url: str | None = None
        if api_key is None:
            self.api_key = os.environ.get("BFL_API_KEY")
        else:
            self.api_key = api_key

    async def request(self):
        """
        Request to generate the image.
        """
        if self.request_id is not None:
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/v1/{API_ENDPOINTS[self.name]}",
                headers={
                    "accept": "application/json",
                    "x-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=self.request_json,
            )
            result = response.json()
            if response.status_code != 200:
                raise ApiException(status_code=response.status_code, detail=result.get("detail"))
            self.request_id = response.json()["id"]

    async def retrieve(self) -> dict:
        """
        Wait for the generation to finish and retrieve response.
        """
        if self.request_id is None:
            await self.request()
        while self.result is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_URL}/v1/get_result",
                    headers={
                        "accept": "application/json",
                        "x-key": self.api_key,
                    },
                    params={
                        "id": self.request_id,
                    },
                )
                result = response.json()
                if "status" not in result:
                    raise ApiException(status_code=response.status_code, detail=result.get("detail"))
                elif result["status"] == "Ready":
                    self.result = result["result"]
                elif result["status"] == "Pending":
                    await asyncio.sleep(0.5)
                else:
                    raise ApiException(
                        status_code=200,
                        detail=f"API returned status '{result['status']}'",
                    )
        return self.result

    async def get_bytes(self) -> bytes:
        """
        Generated image as bytes.
        """
        if self._image_bytes is None:
            url = await self.get_url()
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    self._image_bytes = response.content
                else:
                    raise ApiException(status_code=response.status_code)
        return self._image_bytes

    async def get_url(self) -> str:
        """
        Public url to retrieve the image from
        """
        if self._url is None:
            result = await self.retrieve()
            self._url = result["sample"]
        return self._url

    async def get_image(self) -> Image.Image:
        """
        Load the image as a PIL Image
        """
        bytes_data = await self.get_bytes()
        return Image.open(io.BytesIO(bytes_data))

    async def save(self, path: str) -> str:
        """
        Save the generated image to a local path

        Args:
            path: The path to save the image to

        Returns:
            The full path where the image was saved
        """
        url = await self.get_url()
        suffix = Path(url).suffix
        if not path.endswith(suffix):
            path = path + suffix
        Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
        bytes_data = await self.get_bytes()
        with open(path, "wb") as file:
            file.write(bytes_data)
        return path


class FluxBflTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.generation]
        self.description = "Generate an image using the Flux API and save it to a local file."
        self.settings = Settings()

    def init_tool(self) -> Tool:
        return Tool(
            function=self._flux_generate_image,
            name="generate_image_with_flux",
            description=self.description,
        )

    async def _flux_generate_image(
        self,
        prompt: Annotated[str, Field(description="The text prompt for image generation")],
        output_dir: Annotated[str, Field(description="The directory to save the image")],
        model_name: Annotated[
            str, Field(default="flux.1.1-pro", description="The model version to use")
        ] = "flux.1.1-pro",
        width: Annotated[int | None, Field(default=None, description="Width of the image in pixels")] = None,
        height: Annotated[int | None, Field(default=None, description="Height of the image in pixels")] = None,
        seed: Annotated[int | None, Field(default=None, description="Seed for reproducibility")] = None,
    ) -> dict[str, Any]:
        """Generate an image using the Flux API and save it to a local file.

        Args:
            prompt: The text prompt for image generation
            output_dir: The directory to save the image
            model_name: The model version to use (default: flux.1.1-pro)
            width: Width of the image in pixels (must be a multiple of 32, between 256 and 1440)
            height: Height of the image in pixels (must be a multiple of 32, between 256 and 1440)
            seed: Optional seed for reproducibility

        Returns:
            A dictionary containing information about the generated image
        """

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir).expanduser().resolve()
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate a filename based on the prompt
            filename = "_".join(prompt.split()[:5]).lower()
            filename = "".join(c if c.isalnum() or c == "_" else "_" for c in filename)
            if len(filename) > 50:
                filename = filename[:50]

            # Full path for the image (extension will be added by the save method)
            image_path = output_path / filename

            logger.info(f"Generating image with prompt: {prompt}")

            # Create image request
            image_request = ImageRequest(
                prompt=prompt,
                name=model_name,
                width=width,
                height=height,
                seed=seed,
                api_key=self.settings.bfl_api_key,
                validate=True,
            )

            # Request and save the image
            logger.info("Requesting image from Flux API...")
            await image_request.request()

            logger.info("Waiting for image generation to complete...")
            await image_request.retrieve()

            logger.info("Saving image to disk...")
            saved_path = await image_request.save(str(image_path))

            # Get the image URL
            image_url = await image_request.get_url()
        except ApiException as e:
            return {
                "success": False,
                "error": f"API error: {e}",
                "message": f"Failed to generate image: {e}",
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Invalid parameters: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate image: {e}",
            }
        else:
            return {
                "success": True,
                "prompt": prompt,
                "model": model_name,
                "image_path": saved_path,
                "image_url": image_url,
                "message": f"Successfully generated and saved image to {saved_path}",
            }


@hookimpl
def register(manager):
    settings = Settings()
    if settings.bfl_api_key:
        manager.register(FluxBflTool())
