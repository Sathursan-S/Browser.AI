from livekit.agents import Agent, JobContext, WorkerOptions, cli
from livekit.plugins import silero, piper
from langchain_google_genai import ChatGoogleGenerativeAI
import os

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ.get("GOOGLE_API_KEY"))

    # Download the Piper TTS model if it's not already downloaded
    model_path = "en_US-lessac-medium.onnx"
    if not os.path.exists(model_path):
        piper.download_voice(model_path)

    agent = Agent(
        llm=llm,
        tts=piper.TTS(model=model_path),
        vad=silero.VAD.load(),
    )

    await agent.start(ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
