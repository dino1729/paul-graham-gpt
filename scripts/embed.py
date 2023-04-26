import os
import json
import time

from openai import Configuration, OpenAiApi
from supabase_py import create_client


openai_api_key = os.getenv("AZURE_OPENAI_APIKEY")
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_embedding = os.getenv("AZURE_OPENAI_EMBEDDING")
openai_version = os.getenv("AZURE_OPENAI_VERSION")

base_url = f"{openai_endpoint}openai/deployments/{openai_embedding}"

def generate_embeddings(essays):
    configuration = Configuration(
        base_path=base_url,
        api_key=openai_api_key
    )
    openai = OpenAiApi(configuration=configuration)

    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    for i, section in enumerate(essays):
        for j, chunk in enumerate(section["chunks"]):
            essay_title = chunk["essay_title"]
            essay_url = chunk["essay_url"]
            essay_date = chunk["essay_date"]
            essay_thanks = chunk["essay_thanks"]
            content = chunk["content"]
            content_length = chunk["content_length"]
            content_tokens = chunk["content_tokens"]

            embedding_response = openai.create_embedding(
                model=openai_embedding,
                input_=content,
                options={
                    "api_key": openai_api_key,
                    "parameters": {
                        "api_version": openai_version
                    }
                }
            )

            embedding = embedding_response["data"]["data"][0]["embedding"]

            data, error = supabase.table("pg").insert({
                "essay_title": essay_title,
                "essay_url": essay_url,
                "essay_date": essay_date,
                "essay_thanks": essay_thanks,
                "content": content,
                "content_length": content_length,
                "content_tokens": content_tokens,
                "embedding": embedding
            }).execute()

            if error:
                print("error", error)
            else:
                print(f"saved {i}, {j} {essay_title} {content_tokens}")

            time.sleep(0.8)


if __name__ == '__main__':
    with open('scripts/pg.json', 'r') as f:
        book = json.load(f)
    
    generate_embeddings(book["essays"])
