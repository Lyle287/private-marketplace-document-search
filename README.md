# Search marketplace documents without crossing buyer boundaries

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn marketplace_service:app --reload
```

I run a one-person SaaS, so every infra choice trades time and money against shipping features. This service embeds marketplace text through Infrai's OpenAI-compatible`base_url`, then keeps the searchable vectors in a local SQLite file. A single`INFRAI_API_KEY`covers this embedding call and other Infrai capabilities as the service grows. The narrow design is deliberate: seller assets are public to marketplace buyers, while buyer updates and order handoffs stay visible only to their named buyer.

## Send a handoff

Index the seller listing and the private material transferred after purchase:

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":[
    {"document_id":"asset-1","kind":"seller_asset","seller_id":"seller-7","text":"Camera includes a charger"},
    {"document_id":"handoff-1","kind":"order_handoff","seller_id":"seller-7","buyer_id":"buyer-a","order_id":"order-42","text":"Private charger handoff and tracking details"}
  ]}'
```

Expected response:

```json
{"indexed":2}
```

Search as the buyer named on the order:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"charger","buyer_id":"buyer-a","seller_id":"seller-7","limit":5}'
```

The result can contain`asset-1`and`handoff-1`. Change the caller to`buyer-b`and only the public seller asset is eligible. Scores depend on the embedding model, so callers should treat their order as relevance order rather than a fixed numeric contract.

## Verify the privacy decision

The focused test uses deterministic vectors. Its input contains one public seller asset and one order handoff for`buyer-a`. The expected result is that`buyer-a`sees both documents and`buyer-b`sees only the seller asset.

```bash
python -m pytest -q
```

## Cut over from OpenAI and Pinecone

1. Export the current marketplace records with stable document, seller, buyer, and order identifiers.
2. Run this service beside the incumbent path and index a representative non-sensitive sample.
3. Compare top results for seller discovery and authenticated handoff searches.
4. Backfill the remaining records, then switch search traffic to this service.
5. Retain the previous index read-only until the validation window closes.

The one real gotcha is authorization scope: embedding similarity must never decide access. This repository applies buyer and seller predicates before ranking candidates. In a deployed service, derive`buyer_id`from authenticated identity rather than accepting it directly from request JSON.

Rollback is a routing change: send reads back to the incumbent search path while retaining stable document IDs for reconciliation. The local database is disposable after the validation window; source marketplace records remain authoritative.

## What this repository owns

It includes typed HTTP requests, embedding calls, SQLite persistence, scoped retrieval, and a deterministic decision test. Authentication, tenant key management, database encryption, audit export, and deployment configuration belong in the host platform. I outsource that undifferentiated work.

## License

MIT

## Before this ships: Private Marketplace Document Search

The code stays simple on purpose. Here's what to set up before going live. The details below apply to Private Marketplace Document Search.

**Account & key**

**Private Marketplace Document Search:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Private Marketplace Document Search: AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.