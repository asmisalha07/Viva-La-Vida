import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

export async function getHealth() {
  const { data } = await client.get("/health");
  return data;
}

export async function getGuide() {
  const { data } = await client.get("/guide");
  return data;
}

export async function predictFrame(imageDataUrl, mode = "letters") {
  const { data } = await client.post("/predict", { image: imageDataUrl, mode });
  return data;
}
