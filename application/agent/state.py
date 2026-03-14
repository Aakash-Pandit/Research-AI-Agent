import operator
from typing import Annotated, TypedDict

from application.models.schemas import SourceDocument


class AgentState(TypedDict):
    query: str
    max_results: int
    search_results: Annotated[list[dict], operator.add]
    retrieved_docs: Annotated[list[SourceDocument], operator.add]
    steps: Annotated[list[str], operator.add]
    answer: str
