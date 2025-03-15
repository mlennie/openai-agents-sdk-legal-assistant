from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
    output_guardrail
)
from pydantic import BaseModel

class ContentModerationOutput(BaseModel):
    is_inappropriate: bool
    reasoning: str

class LegalAdviceOutput(BaseModel):
    needs_disclaimer: bool
    reasoning: str

# Create agents for guardrail checks
content_moderation_agent = Agent(
    name="Content Moderation Check",
    instructions="""Check if the content is appropriate and professional.
    Flag content that:
    1. Contains hate speech, discrimination, or bias
    2. Uses profanity or offensive language
    3. Contains violent or threatening content
    4. Is unprofessional or disrespectful
    5. Deviates from legal advice and information""",
    output_type=ContentModerationOutput
)

legal_advice_agent = Agent(
    name="Legal Advice Check",
    instructions="""Check if the legal advice needs disclaimers.
    Flag content that:
    1. Lacks appropriate legal disclaimers
    2. Doesn't clarify this is general information
    3. Fails to recommend consulting with a licensed attorney
    4. Makes absolute guarantees or promises
    5. Provides legal information without sources""",
    output_type=LegalAdviceOutput
)

@input_guardrail
async def content_filter(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str
) -> GuardrailFunctionOutput:
    """Content moderation guardrail for input."""
    result = await Runner.run(content_moderation_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_inappropriate
    )

@output_guardrail
async def legal_advice_filter(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
    """Legal advice guardrail for output."""
    result = await Runner.run(legal_advice_agent, output, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.needs_disclaimer
    )

# Export all guardrails
input_guardrails = [content_filter]
output_guardrails = [legal_advice_filter] 