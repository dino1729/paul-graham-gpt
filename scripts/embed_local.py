import os
import json
import time

from openai import Configuration, OpenAiApi
from csv import writer


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

    with open("scripts/embeddings.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["essay_title", "essay_url", "essay_date", "essay_thanks", "content", "content_length", "content_tokens", "embedding"])

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

                writer.writerow([
                    essay_title,
                    essay_url,
                    essay_date,
                    essay_thanks,
                    content,
                    content_length,
                    content_tokens,
                    embedding
                ])


if __name__ == '__main__':
    with open('scripts/pg.json', 'r') as f:
        book = json.load(f)
    
    generate_embeddings(book["essays"])
