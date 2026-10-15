from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class AssetKind(StrEnum):
    SELLER_ASSET = "seller_asset"
    BUYER_UPDATE = "buyer_update"
    ORDER_HANDOFF = "order_handoff"


class MarketplaceDocument(BaseModel):
    document_id: str = Field(min_length=1)
    kind: AssetKind
    seller_id: str = Field(min_length=1)
    buyer_id: str | None = None
    order_id: str | None = None
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_private_scope(self) -> "MarketplaceDocument":
        if self.kind != AssetKind.SELLER_ASSET and not self.buyer_id:
            raise ValueError("buyer_id is required for buyer updates and order handoffs")
        if self.kind == AssetKind.ORDER_HANDOFF and not self.order_id:
            raise ValueError("order_id is required for order handoffs")
        return self


class IndexRequest(BaseModel):
    documents: list[MarketplaceDocument] = Field(min_length=1)


class IndexResult(BaseModel):
    indexed: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    buyer_id: str = Field(min_length=1)
    seller_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    document_id: str
    kind: AssetKind
    text: str
    score: float


class SearchResult(BaseModel):
    hits: list[SearchHit]

