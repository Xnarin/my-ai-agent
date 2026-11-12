from vector_store import open_vector_store
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


def search(query):
    with open_vector_store() as vector_store:
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
        return retriever.invoke(query)


if __name__ == "__main__":
    query = "react"
    for document in search(query):
        print(document.page_content)
