import { OpenAIModel } from "@/types";
import { createClient } from "@supabase/supabase-js";
import { createParser, ParsedEvent, ReconnectInterval } from "eventsource-parser";
import { loadEnvConfig } from "@next/env";
import { Configuration, OpenAIApi } from "openai";

loadEnvConfig("");

const apikey = process.env.AZURE_OPENAI_APIKEY;
const baseurl = process.env.AZURE_OPENAI_ENDPOINT;
const deploymentname = process.env.AZURE_OPENAI_DEPLOYMENT;
const modelname = process.env.AZURE_OPENAI_MODEL;

let model_url = `${baseurl}openai/deployments/${modelname}`;
let modelurl = `${baseurl}openai/deployments/${modelname}/completions?api-version=2022-12-01`;

export const supabaseAdmin = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);

export const OpenAIStream = async (prompt: string, apiKey: string) => {
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const configuration = new Configuration({
    basePath: model_url,
    apiKey: apikey,
  });
  const openai = new OpenAIApi(configuration);

  // const res = await fetch("https://api.openai.com/v1/chat/completions", {
  //   headers: {
  //     "Content-Type": "application/json",
  //     Authorization: `Bearer ${apiKey}`
  //   },
  //   method: "POST",
  //   body: JSON.stringify({
  //     model: OpenAIModel.DAVINCI_TURBO,
  //     messages: [
  //       {
  //         role: "system",
  //         content: "You are a helpful assistant that accurately answers queries using Paul Graham's essays. Use the text provided to form your answer, but avoid copying word-for-word from the essays. Try to use your own words when possible. Keep your answer under 5 sentences. Be accurate, helpful, concise, and clear."
  //       },
  //       {
  //         role: "user",
  //         content: prompt
  //       }
  //     ],
  //     max_tokens: 150,
  //     temperature: 0.0,
  //     stream: true
  //   })
  // });
  const res = await openai.createCompletion({
    deployment: "gpt-3p5-turbo",
    messages: [
      {
        role: "system",
        content: "You are a helpful assistant that accurately answers queries using Paul Graham's essays. Use the text provided to form your answer, but avoid copying word-for-word from the essays. Try to use your own words when possible. Keep your answer under 5 sentences. Be accurate, helpful, concise, and clear."
      },
      {
        role: "user",
        content: prompt
      }
    ],
    max_tokens: 150,
    temperature: 0.0,
    stream: true
  },
  {
    headers: {
      "api-key": apikey,
    },
    params: {
      "api-version": "2022-12-01",
    },
  });

  if (res.status !== 200) {
    throw new Error("OpenAI API returned an error");
  }

  const stream = new ReadableStream({
    async start(controller) {
      const onParse = (event: ParsedEvent | ReconnectInterval) => {
        if (event.type === "event") {
          const data = event.data;

          if (data === "[DONE]") {
            controller.close();
            return;
          }

          try {
            const json = JSON.parse(data);
            const text = json.choices[0].delta.content;
            const queue = encoder.encode(text);
            controller.enqueue(queue);
          } catch (e) {
            controller.error(e);
          }
        }
      };

      const parser = createParser(onParse);

      for await (const chunk of res.body as any) {
        parser.feed(decoder.decode(chunk));
      }
    }
  });

  return stream;
};
