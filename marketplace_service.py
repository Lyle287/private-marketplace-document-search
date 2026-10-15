import os

from fastapi import FastAPI

from marketplace_search.embeddings_client import InfraiEmbeddings
from marketplace_search.index import MarketplaceIndex
from marketplace_search.models import IndexRequest, IndexResult, SearchRequest, SearchResult

app = FastAPI(title="Marketplace document search")
index = MarketplaceIndex(os.environ.get("MARKETPLACE_DB", "marketplace.db"), InfraiEmbeddings())


@app.post("/documents", response_model=IndexResult)
def index_documents(request: IndexRequest) -> IndexResult:
    return IndexResult(indexed=index.add(request.documents))


@app.post("/search", response_model=SearchResult)
def search_documents(request: SearchRequest) -> SearchResult:
    return SearchResult(
        hits=index.search(request.query, request.buyer_id, request.seller_id, request.limit)
    )

