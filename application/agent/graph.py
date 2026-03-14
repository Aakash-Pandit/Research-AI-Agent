from langgraph.graph import END, START, StateGraph

from application.agent.nodes import generate_answer, retrieve_docs, search_web
from application.agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("search_web", search_web)
    graph.add_node("retrieve_docs", retrieve_docs)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "search_web")
    graph.add_edge("search_web", "retrieve_docs")
    graph.add_edge("retrieve_docs", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


agent = build_graph()
