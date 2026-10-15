from collections.abc import Sequence

from marketplace_search.index import MarketplaceIndex
from marketplace_search.models import AssetKind, MarketplaceDocument


class KeywordEmbeddings:
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float("charger" in text.lower()), float("tracking" in text.lower())]
            for text in texts
        ]


def test_search_keeps_order_handoff_with_its_buyer() -> None:
    index = MarketplaceIndex(":memory:", KeywordEmbeddings())
    index.add(
        [
            MarketplaceDocument(
                document_id="asset-1",
                kind=AssetKind.SELLER_ASSET,
                seller_id="seller-7",
                text="Camera includes a charger",
            ),
            MarketplaceDocument(
                document_id="handoff-1",
                kind=AssetKind.ORDER_HANDOFF,
                seller_id="seller-7",
                buyer_id="buyer-a",
                order_id="order-42",
                text="Private charger handoff and tracking details",
            ),
        ]
    )

    buyer_a = index.search("charger", "buyer-a", "seller-7", 5)
    buyer_b = index.search("charger", "buyer-b", "seller-7", 5)

    assert {hit.document_id for hit in buyer_a} == {"handoff-1", "asset-1"}
    assert [hit.document_id for hit in buyer_b] == ["asset-1"]
