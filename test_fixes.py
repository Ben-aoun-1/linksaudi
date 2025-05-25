from market_reports.rag_enhanced import get_weaviate_client

client = get_weaviate_client()

# Test simple document retrieval
result = (
    client.query
    .get("LegalDocument", ["content", "documentTitle", "documentType"])
    .with_limit(3)
    .do()
)

print("Result:", result)
if result and "data" in result:
    docs = result["data"]["Get"].get("LegalDocument", [])
    print(f"Found {len(docs)} documents!")
    for doc in docs:
        print(f"- {doc.get('documentTitle', 'No title')}")