import os
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from tools import internet_search
from dotenv import load_dotenv
load_dotenv()

llm = ChatOllama(
    model="gpt-oss:120b-cloud", # Use the model you pulled
    base_url="http://localhost:11434", # Point to the local Ollama server
    temperature=0
)


agent_graph = create_deep_agent(
    model=llm,
    tools=[internet_search],
    checkpointer=MemorySaver() # This enables Short-Term Chat Memory
)

# 4. CHAT INTERFACE
def start_chat_session(session_id: str):
    """
    Runs a continuous chat loop for a specific session ID.
    """
    print(f"\n🔵 Starting new session: {session_id}")
    print("Type 'exit' to quit or 'new' to start a fresh conversation.\n")

    config = {"configurable": {"thread_id": session_id}}

    while True:
        user_input = input(f"User ({session_id}): ")

        if user_input.lower() == "exit":
            break
        if user_input.lower() == "new":
            return "new" # Signal to restart

        # Stream the agent's thought process
        print("🤖 Deep Agent is thinking...")

        # The agent returns a stream of events (planning, tool calls, answers)
        events = agent_graph.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )

        final_answer = ""
        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                # Filter out intermediate tool calls, show only AI response
                if last_msg.type == "ai" and not last_msg.tool_calls:
                    final_answer = last_msg.content

        print(f"Agent: {final_answer}\n")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    current_session = "session_1"

    while True:
        result = start_chat_session(current_session)
        if result == "new":
            # Simple logic to increment session ID for a "new chat" feel
            current_session = f"session_{int(current_session.split('_')[1]) + 1}"
            print(f"\n--- Switching to {current_session} ---\n")
        else:
            break