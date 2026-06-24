




async def get_relevant_chunks(query: str, user_id: int, db: Session) -> str:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    query_vector = result.embeddings[0].values

    results = db.execute(
        select(models.Chunk)
        .order_by(models.Chunk.embedding.cosine_distance(query_vector))
        .limit(5)
    ).scalars().all()
    return "\n\n".join([chunk.text for chunk in results])




    # 1. embed the query
    # 2. find similar chunks
    # 3. return them as a single string to inject into the prompt