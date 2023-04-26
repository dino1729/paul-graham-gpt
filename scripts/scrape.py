from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import gpt3_tokenizer
import json
import re

BASE_URL = "http://www.paulgraham.com/"
CHUNK_SIZE = 200

class PGChunk:
    def __init__(self, essay_title: str, essay_url: str, essay_date: str, essay_thanks: str, content: str, content_length: int, content_tokens: int, embedding: List[float]):
        self.essay_title = essay_title
        self.essay_url = essay_url
        self.essay_date = essay_date
        self.essay_thanks = essay_thanks
        self.content = content
        self.content_length = content_length
        self.content_tokens = content_tokens
        self.embedding = embedding

class PGEssay:
    def __init__(self, title: str, url: str, date: str, thanks: str, content: str, length: int, tokens: int, chunks: List[PGChunk]):
        self.title = title
        self.url = url
        self.date = date
        self.thanks = thanks
        self.content = content
        self.length = length
        self.tokens = tokens
        self.chunks = chunks

class PGJSON:
    def __init__(self, current_date: str, author: str, url: str, length: int, tokens: int, essays: List[PGEssay]):
        self.current_date = current_date
        self.author = author
        self.url = url
        self.length = length
        self.tokens = tokens
        self.essays = essays

def getLinks() -> List[Dict[str, str]]:
    html = requests.get(f"{BASE_URL}articles.html").text
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    linksArr = []

    for i, table in enumerate(tables):
        if i == 2:
            links = table.find_all("a")

            for link in links:
                url = link.get("href")
                title = link.text

                if url and url.endswith(".html"):
                    linkObj = {
                        "url": url,
                        "title": title
                    }

                    linksArr.append(linkObj)

    return linksArr

def getEssay(linkObj: Dict[str, str]) -> PGEssay:
    title = linkObj["title"]
    url = linkObj["url"]

    essay = PGEssay("", "", "", "", "", 0, 0, [])

    fullLink = BASE_URL + url
    print(fullLink)
    html = requests.get(fullLink).text
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    for i, table in enumerate(tables):
        if i == 1:
            text = table.text

            cleanedText = text.replace("\s+", " ")
            cleanedText = cleanedText.replace("\.([a-zA-Z])", ". $1")

            date = re.search("([A-Z][a-z]+ [0-9]{4})", cleanedText)
            dateStr = ""
            textWithoutDate = ""

            if date:
                dateStr = date.group(0)
                textWithoutDate = cleanedText.replace(date.group(0), "")

            essayText = textWithoutDate.replace("\n", " ")
            thanksTo = ""

            split = essayText.split(". ")
            lastSentence = split[-1]

            if lastSentence and "Thanks to" in lastSentence:
                thanksToSplit = lastSentence.split("Thanks to")

                if thanksToSplit[1].strip()[-1] == ".":
                    thanksTo = "Thanks to " + thanksToSplit[1].strip()
                else:
                    thanksTo = "Thanks to " + thanksToSplit[1].strip() + "."

                essayText = essayText.replace(thanksTo, "")

            trimmedContent = essayText.strip()
            print(len(trimmedContent))
            print(len(gpt3_tokenizer.encode(trimmedContent)))
            essay = PGEssay(title, fullLink, dateStr, thanksTo.strip(), trimmedContent, len(trimmedContent), len(gpt3_tokenizer.encode(trimmedContent)), [])
            print("Essay: " + title)

    return essay

def chunkEssay(essay: PGEssay) -> PGEssay:
    title = essay.title
    url = essay.url
    date = essay.date
    thanks = essay.thanks
    content = essay.content
    print("Chunking essay: " + title)

    essayTextChunks = []

    if len(gpt3_tokenizer.encode(content)) > CHUNK_SIZE:
        split = content.split(". ")
        chunkText = ""

        for sentence in split:
            sentenceTokenLength = len(gpt3_tokenizer.encode(sentence))
            chunkTextTokenLength = len(gpt3_tokenizer.encode(chunkText))

            if chunkTextTokenLength + sentenceTokenLength > CHUNK_SIZE:
                essayTextChunks.append(chunkText)
                chunkText = ""

            if sentence[-1].isalnum():
                chunkText += sentence + ". "
            else:
                chunkText += sentence + " "

        essayTextChunks.append(chunkText.strip())
    else:
        essayTextChunks.append(content.strip())

    essayChunks = []

    for text in essayTextChunks:
        trimmedText = text.strip()

        chunk = PGChunk(title, url, date, thanks, trimmedText, len(trimmedText), len(gpt3_tokenizer.encode(trimmedText)), [])

        essayChunks.append(chunk)

    if len(essayChunks) > 1:
        for i, chunk in enumerate(essayChunks):
            if chunk.content_tokens < 100 and i > 0:
                prevChunk = essayChunks[i - 1]
                prevChunk.content += " " + chunk.content
                prevChunk.content_length += chunk.content_length
                prevChunk.content_tokens += chunk.content_tokens
                essayChunks.pop(i)

    chunkedSection = PGEssay(title, url, date, thanks, content, len(content), len(gpt3_tokenizer.encode(content)), essayChunks)

    return chunkedSection

def main():
    links = getLinks()
    print("There are a total of " + str(len(links)) + " essays.")

    essays = []

    for link in links:
        print("Getting essay: " + link["title"])
        essay = getEssay(link)
        chunkedEssay = chunkEssay(essay)
        essays.append(chunkedEssay)

    json_obj = PGJSON("2023-04-25", "Paul Graham", "http://www.paulgraham.com/articles.html", sum([essay.length for essay in essays]), sum([essay.tokens for essay in essays]), essays)

    with open("scripts/pg.json", "w") as f:
        json.dump(json_obj.__dict__, f)

if __name__ == "__main__":
    main()
