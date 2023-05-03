import json
import time
from enum import Enum

from openai import Configuration, OpenAiApi
from supabase_py import create_client
from dotenv import load_dotenv
import os


load_dotenv()  # loading environment variables from .env file


# Enum for constants
class Constants(Enum):
    OPENAI_API_KEY = os.getenv("AZURE_OPENAI_APIKEY")
    OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_EMBEDDING = os.getenv("AZURE_OPENAI_EMBEDDING")
    OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION")


OPENAI_BASE_URL = f"{Constants.OPENAI_ENDPOINT.value}openai/deployments/{Constants.OPENAI_EMBEDDING.value}"


# Generate embeddings for essays
def generate_embeddings(essays):
    configuration = Configuration(
        base_path=OPENAI_BASE_URL,
        api_key=Constants.OPENAI_API_KEY.value
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

            # use try-except block for error handling
            try:
                embedding_response = openai.create_embedding(
                    model=Constants.OPENAI_EMBEDDING.value,
                    input_=content,
                    options={
                        "api_key": Constants.OPENAI_API_KEY.value,
                        "parameters": {
                            "api_version": Constants.OPENAI_VERSION.value
                        }
                    }
                )
                
                #extracting the embeddings
                embedding = embedding_response["data"]["data"][0]["embedding"]
                
                # insert data and handling supabase errors
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
            
            except Exception as e:
                print(f"error processing essay {i}, {j}, {e}")
    

if __name__ == '__main__':
    with open('scripts/pg.json', 'r') as f:
        book = json.load(f)

    generate_embeddings(book["essays"])
