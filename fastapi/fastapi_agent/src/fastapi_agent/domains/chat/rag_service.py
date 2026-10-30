from time import perf_counter

from langgraph.graph.state import CompiledStateGraph


class RagChatService:
    async def stream_rag(self, agent: CompiledStateGraph, question: str):
        started = perf_counter()
        answer = ""
        sources = []

        yield "status", {"message": "문서를 검색하고 있습니다."}

        async for mode, data in agent.astream(
            {"question": question},
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                chunk, metadata = data
                if metadata["langgraph_node"] == "generate" and chunk.text:
                    yield "token", {"content": chunk.text}

            elif mode == "updates":
                if "retrieve" in data:
                    documents = data["retrieve"]["documents"]
                    sources = [
                        {
                            "id": index,
                            "source": document.metadata["source"],
                            "page_number": document.metadata["page_number"],
                        }
                        for index, document in enumerate(documents, start=1)
                    ]
                    yield "sources", {"sources": sources}
                    yield "status", {"message": "답변을 생성하고 있습니다."}

                if "generate" in data:
                    answer = data["generate"]["answer"]

        yield "done", {
            "answer": answer,
            "sources": sources,
            "elapsed_ms": round((perf_counter() - started) * 1000),
        }


rag_chat_service = RagChatService()
