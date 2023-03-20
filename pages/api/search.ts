import { supabaseAdmin } from "@/utils";
import { loadEnvConfig } from "@next/env";
import { Configuration, OpenAIApi } from "openai";

export const config = {
  runtime: "edge"
};

loadEnvConfig("");
const apikey = process.env.AZURE_OPENAI_APIKEY;
//const baseurl = process.env.AZURE_OPENAI_ENDPOINT;
//const deploymentname = process.env.AZURE_OPENAI_DEPLOYMENT;
//let base_url = `${baseurl}openai/deployments/${deploymentname}`;
//let url = `${baseurl}openai/deployments/${deploymentname}/embeddings?api-version=2022-12-01`;

const handler = async (req: Request): Promise<Response> => {
  
  // const configuration = new Configuration({
  //   basePath: base_url,
  //   apiKey: apikey,
  // });
  // const openai = new OpenAIApi(configuration);

  try {
    const { query, userapiKey, matches } = (await req.json()) as {
      query: string;
      userapiKey: string;
      matches: number;
    };

    const input = query.replace(/\n/g, " ");

    const res = await fetch("https://textllmapi.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2022-12-01", {
      headers: {
        "Content-Type": "application/json",
        "api-key": apikey
      },
      method: "POST",
      body: JSON.stringify({
        deployment: "text-embedding-ada-002",
        input
      })
    });

    // const res = await openai.createEmbedding({
    //   deployment: "text-embedding-ada-002",
    //   input
    // },
    // {
    //   headers: {
    //     "api-key": apikey,
    //   },
    //   params: {
    //     "api-version": "2022-12-01",
    //   },
    // });

    const json = await res.json();
    const embedding = json.data[0].embedding;

    const { data: chunks, error } = await supabaseAdmin.rpc("pg_search", {
      query_embedding: embedding,
      similarity_threshold: 0.01,
      match_count: matches
    });

    if (error) {
      console.error(error);
      return new Response("Error", { status: 500 });
    }

    return new Response(JSON.stringify(chunks), { status: 200 });
  } catch (error) {
    console.error(error);
    return new Response("Error", { status: 500 });
  }
};

export default handler;
