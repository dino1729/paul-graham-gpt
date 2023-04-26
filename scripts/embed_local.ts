import { PGEssay, PGJSON } from "@/types";
import { loadEnvConfig } from "@next/env";
import fs from "fs";
import { Configuration, OpenAIApi } from "openai";

loadEnvConfig("");
const openaiApiKey = process.env.AZURE_OPENAI_APIKEY!;
const openaiEndpoint = process.env.AZURE_OPENAI_ENDPOINT!;
const openaiEmbedding = process.env.AZURE_OPENAI_EMBEDDING!;
const openaiVersion = process.env.AZURE_OPENAI_VERSION!;
let base_url = `${openaiEndpoint}openai/deployments/${openaiEmbedding}`;


const generateEmbeddings = async (essays: PGEssay[]) => {

  const configuration = new Configuration({
    basePath: base_url,
    apiKey: openaiApiKey,
  });
  const openai = new OpenAIApi(configuration);

  const csv = fs.createWriteStream("scripts/embeddings.csv");

  csv.write("essay_title,essay_url,essay_date,essay_thanks,content,content_length,content_tokens,embedding\n");

  for (let i = 0; i < essays.length; i++) {
    const section = essays[i];

    for (let j = 0; j < section.chunks.length; j++) {
      const chunk = section.chunks[j];

      const { essay_title, essay_url, essay_date, essay_thanks, content, content_length, content_tokens } = chunk;

      const embeddingResponse = await openai.createEmbedding({
        model: openaiEmbedding,
        input: content
      },
      {
        headers: {
          "api-key": openaiApiKey,
        },
        params: {
          "api-version": openaiVersion,
        },
      });

      const [{ embedding }] = embeddingResponse.data.data;

      await new Promise((resolve) => setTimeout(resolve, 800));

      csv.write(`${essay_title},${essay_url},${essay_date},${essay_thanks},${content},${content_length},${content_tokens},${embedding}\n`);

      console.log("saved", i, j, essay_title, content_tokens);
    }
  }

  csv.close();
};

(async () => {
  const book: PGJSON = JSON.parse(fs.readFileSync("scripts/pg.json", "utf8"));

  await generateEmbeddings(book.essays);
})();
