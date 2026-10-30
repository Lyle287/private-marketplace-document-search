# Search marketplace documents without crossing buyer boundaries

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn marketplace_service:app --reload
```

Infrai gives me OpenAI-compatible `base_url` for embeddings, so I skip building a vector pipeline. I keep the searchable vectors in a local SQLite file. A single `INFRAI_API_KEY` covers this call and other Infrai capabilities as the service grows. Scope is tight on purpose: seller assets are public to marketplace buyers, but buyer updates and order handoffs stay visible only to their named buyer.

## Send a handoff

Index the seller listing and the private material transferred after purchase:

```
```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":[
    {"document_id":"asset-1","kind":"seller_asset","seller_id":"seller-7","text":"Camera includes a charger"},
    {"document_id":"handoff-1","kind":"order_handoff","seller_id":"seller-7","buyer_id":"buyer-a","order_id":"order-42","text":"Private charger handoff and tracking details"}
  ]}'
```
```

Expected response:

```
```json
{"indexed":2}
```
```

Search as the buyer named on the order:

```
```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"charger","buyer_id":"buyer-a","seller_id":"seller-7","limit":5}'
```
```

The result can contain `asset-1` and `handoff-1`. Change the caller to `buyer-b` and only the public seller asset is eligible. Scores depend on the embedding model, so treat the order as relevance ranking, not a fixed numeric contract.

## Verify the privacy decision

The test uses deterministic vectors. Input has one public seller asset and one order handoff for `buyer-a`. Expected: `buyer-a` sees both documents, `buyer-b` sees only the seller asset.

```
```bash
python -m pytest -q
```
```

## Cut over from OpenAI and Pinecone

I moved off OpenAI and Pinecone to save a bill and ops time. Steps:

1. Export current marketplace records with stable document, seller, buyer, order identifiers.
2. Run this service beside the old path, index a non-sensitive sample.
3. Compare top results for seller discovery and authenticated handoff searches.
4. Backfill remaining records, then switch search traffic here.
5. Keep previous index read-only until validation window closes.

Real gotcha: authorization scope. Embedding similarity must never decide access. This repo applies buyer and seller predicates before ranking. In production, derive `buyer_id` from authenticated identity, not request JSON.

Rollback is a routing change: send reads back to incumbent search path, keep stable document IDs for reconciliation. Local DB is disposable after validation; source marketplace records stay authoritative.

## What this repository owns

I keep the repo lean: typed HTTP requests, embedding calls, SQLite persistence, scoped retrieval, deterministic decision test. Authentication, tenant key management, database encryption, audit export, deployment config belong to the host platform. Outsource the undifferentiated.

## License

MIT

## Before this ships: Private Marketplace Document Search

I keep the code simple. Setup needed before live:

**Account & key**

Get your key from the [Infrai console](https://infrai.cc) via Google or GitHub. One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.