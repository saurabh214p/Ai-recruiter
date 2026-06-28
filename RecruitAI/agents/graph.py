"""
RecruitAI - LangGraph Recruitment Pipeline
Orchestrates the recruiter flow using a LangGraph StateGraph.

Pipeline:
    JD Text → JD Agent → Retrieval Agent → Ranking Agent → Explanation Agent → Results

Each node reads from and writes to the shared RecruitmentState.
Error handling: if any node sets 'error' in state, subsequent nodes
are skipped via conditional edges routing to END.
"""

import logging

from langgraph.graph import END, StateGraph

from agents.jd_agent import JDAgent
from agents.retrieval_agent import RetrievalAgent
from agents.ranking_agent import RankingAgent
from agents.explanation_agent import ExplanationAgent
from embeddings.embedder import Embedder
from embeddings.qdrant_db import QdrantManager
from models.schemas import RecruitmentState

logger = logging.getLogger(__name__)


def _should_continue(state: RecruitmentState) -> str:
    """Routing function: stop pipeline on error, otherwise continue.

    Used as a conditional edge after each node to implement
    fail-fast error handling without try/except in every node.
    """
    if state.get("error"):
        logger.error(f"Pipeline halted due to error: {state['error']}")
        return "end"
    return "continue"


def build_recruitment_graph(
    llm,
    embedder: Embedder,
    qdrant_manager: QdrantManager,
):
    """Build and compile the LangGraph recruitment pipeline.

    Args:
        llm: LangChain LLM instance (Gemini or OpenAI).
        embedder: Embedder instance for generating vectors.
        qdrant_manager: QdrantManager for Qdrant operations.

    Returns:
        Compiled LangGraph application ready for .invoke().

    Usage:
        graph = build_recruitment_graph(llm, embedder, qdrant)
        result = graph.invoke({"jd_text": "We need a Java developer..."})
        candidates = result.get("results", [])
    """
    # Instantiate agents with injected dependencies
    jd_agent = JDAgent(llm=llm)
    retrieval_agent = RetrievalAgent(
        embedder=embedder, qdrant_manager=qdrant_manager
    )
    ranking_agent = RankingAgent(embedder=embedder)
    explanation_agent = ExplanationAgent(llm=llm)

    # Build the state graph
    workflow = StateGraph(RecruitmentState)

    # Add processing nodes
    workflow.add_node("jd_agent", jd_agent)
    workflow.add_node("retrieval_agent", retrieval_agent)
    workflow.add_node("ranking_agent", ranking_agent)
    workflow.add_node("explanation_agent", explanation_agent)

    # Set entry point
    workflow.set_entry_point("jd_agent")

    # Wire edges with error short-circuits
    workflow.add_conditional_edges(
        "jd_agent",
        _should_continue,
        {"continue": "retrieval_agent", "end": END},
    )
    workflow.add_conditional_edges(
        "retrieval_agent",
        _should_continue,
        {"continue": "ranking_agent", "end": END},
    )
    workflow.add_conditional_edges(
        "ranking_agent",
        _should_continue,
        {"continue": "explanation_agent", "end": END},
    )
    workflow.add_edge("explanation_agent", END)

    # Compile into a runnable graph
    compiled = workflow.compile()

    logger.info(
        "Recruitment pipeline compiled: "
        "JD Agent → Retrieval Agent → Ranking Agent → Explanation Agent"
    )

    return compiled
