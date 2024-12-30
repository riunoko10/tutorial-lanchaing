from dotenv import load_dotenv
import os


from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun

from tool_node import BasicToolNode
from chat_state import State
from route import route_tools

import warnings

# Suprimir la advertencia específica
warnings.filterwarnings("ignore", category=UserWarning, message="'api' backend is deprecated")



load_dotenv()

tool = DuckDuckGoSearchRun()

tools = [tool]



graph_builder = StateGraph(State)


LLM = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini")

llm_with_tools = LLM.bind_tools(tools)

def chatbot(state: State):
    return {"messages": llm_with_tools.invoke(state["messages"])}


tool_node = BasicToolNode(tools)

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "END" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)


graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)


graph = graph_builder.compile()


def show_text(event):
    for key, value in event.items():
        if key == "chatbot":
            # Procesar eventos del chatbot
            messages = value.get("messages").content
            if messages:
                print("Chatbot Message:", messages)
        # elif key == "tools":
        #     # Procesar eventos de herramientas
        #     messages = value.get("messages")[0].content
        #     print("Tool Message:", messages)
        #     # if messages:
        #     #     for message in messages:
        #     #         print("Tool Message:", message.get("content"))
        # else:
        #     print("Unknown event type:", key)




def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        # print ("Event:", event)
        show_text(event)
        # for value in event.values():
        #     print("Assistant:", value)
        #     if value.get("messages"):
        #         print("Assistant:", value["messages"].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # print(tool.invoke(user_input))

        stream_graph_updates(user_input)
    except Exception as e:
        # fallback if input() is not available
        # user_input = "What do you know about LangGraph?"
        # print("User: " + user_input)
        # stream_graph_updates(user_input)
        raise RuntimeError(e)
        break