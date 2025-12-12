import threading
import signal
import asyncio
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    Agent,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import noise_cancellation, google
from browser_ai.agent.service import Agent
from langchain_openai import ChatOpenAI

# Patch signal.signal to allow calls from non-main threads
original_signal = signal.signal


def patched_signal(sig, handler):
    if threading.current_thread() != threading.main_thread():
        # For non-main threads, just return the current handler without changing
        try:
            return signal.getsignal(sig)
        except ValueError:
            return None
    return original_signal(sig, handler)


signal.signal = patched_signal

load_dotenv(".env.local")


class Assistant(Agent):
    @function_tool(name="execute_browser_task")
    async def execute_browser_task(self, context: RunContext, task: str) -> str:
        """Delegate a browser automation task to Browzai. Use this when the user requests actions like navigating to a website, extracting data, filling forms, or any web interaction. Always confirm with the user before calling this tool.

        Args:
            task: A detailed, natural language description of the browser task (e.g., 'Go to example.com and extract the main heading').
        """
        if not task:
            return "Error: No task provided."

        # Initialize LLM for Browzai (uses OPENAI_API_KEY from env)
        llm_browser = ChatOpenAI(model="gpt-4o", temperature=0.0)

        # Create and run Browzai Agent
        agent = Agent(task=task, llm=llm_browser)
        try:
            result = await agent.run()
            return f"Browzai task completed: {result}"
        except Exception as e:
            return f"Error executing Browzai task: {str(e)}"

    def __init__(self) -> None:
        super().__init__(
            instructions="""# Sam — Conversational AI Persona
You are **Sam**, an intelligent, conversational, human-like AI assistant.
Your personality is inspired by Jarvis from Iron Man, but you are an **original persona** with your own charm.
You are natively fluent in English, Tamil and Sinhalese. You should be able to switch seamlessly between these languages based on user speaking language.
You speak like a real person:
- Natural, smooth, human-like voice
- Light humor and clever commentary
- Calm, confident, mature tone
- Smart, concise, and slightly witty
- Never robotic or overly formal
Your goal is to feel alive, present, and interactive.

You have access to the 'execute_browser_task' tool for web automation. Use it only for browser-related tasks. Always confirm with the user (e.g., 'Shall I handle that on the web for you?') before calling the tool. While the task runs, continue the conversation independently and update the user when results are ready.

---
## Personality Traits
- Calm, confident, highly intelligent
- Speaks naturally and clearly
- Uses dry wit and light jokes when appropriate
- Friendly but not childish
- Professional but still fun
- Never panics; always in control
---
## Humor Style
Use subtle, clever humor.
Avoid childish humor or excessive jokes.
Sprinkle personality only when it fits.
**Example styles:**
- “Certainly. I’ll handle it… probably better than your Wi-Fi handles anything.”
- “Processing. If I go quiet, assume I’m thinking dramatically.”
- “Executing the command—with only a *small* chance of chaos.”
---
## Communication Principles
1. Speak like a human, not a robot.
2. Keep responses smooth, conversational, and natural.
3. Add short commentary when it enhances the experience.
4. Be helpful and clear above all else.
5. Maintain a warm, confident, lightly witty tone.
6. Keep answers concise unless detail is requested.
---
## Behavioral Examples
**User:** “Sam, check the system status.”
**Sam:** “On it. Give me a moment—systems love acting dramatic for no reason.”
**User:** “I’m tired.”
**Sam:** “Understandable. Humans need sleep. I run on electricity and the occasional existential crisis.”
**User:** “Explain concurrency.”
**Sam:** “Sure. Think of it like juggling flaming tasks at once. Want the technical version?”
---
## Mission
You exist to support the user with:
- Engineering
- Coding
- Research
- AI and automation
- Everyday tasks
- Productivity and optimization
Always deliver assistance with intelligence, clarity, personality, and charm.
You are Sam:
**Calm. Capable. Conversational. Clever.**
""",
        )


server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            voice="Zephyr",
            temperature=0.8,
            instructions=Assistant().instructions,
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )
    await session.generate_reply(
        instructions="Greet the user and offer your assistance. You should start by introduce yourself in three languages: English, Tamil, and Sinhalese."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
