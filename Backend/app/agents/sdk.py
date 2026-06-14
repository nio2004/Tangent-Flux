from typing import TypeVar
import os

from pydantic import BaseModel

from app.core.config import get_settings

T = TypeVar("T", bound=BaseModel)


async def run_structured_agent(name: str, instructions: str, prompt: str, output_type: type[T]) -> T | None:
    settings = get_settings()
    if not settings.use_openai_agents or not settings.openai_api_key:
        return None
    try:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
        from agents import Agent, Runner

        agent = Agent(name=name, instructions=instructions, model=settings.openai_agent_model, output_type=output_type)
        result = await Runner.run(agent, prompt)
        output = result.final_output
        if isinstance(output, output_type):
            return output
        if isinstance(output, dict):
            return output_type.model_validate(output)
        return output_type.model_validate_json(str(output))
    except Exception:
        return None
