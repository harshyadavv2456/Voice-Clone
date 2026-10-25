// Example: call the local voice service from a Node.js/Next.js backend.
import { writeFile } from "node:fs/promises";

const response = await fetch("http://127.0.0.1:8765/v1/audio/speech", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "harsh-voice",
    input: "Hello from a future project, spoken with my personal voice.",
    voice: "harsh_yadav",
    language: "English",
    response_format: "wav"
  })
});

if (!response.ok) {
  throw new Error("Voice API failed: " + response.status + " " + await response.text());
}
const audio = Buffer.from(await response.arrayBuffer());
await writeFile("speech.wav", audio);
console.log("Saved speech.wav");
