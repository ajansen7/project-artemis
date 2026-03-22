#!/usr/bin/env bun
/**
 * Artemis Webhook Channel — receives HTTP POST notifications from the
 * FastAPI scheduler and pushes them into the active Claude Code session.
 *
 * Handles two event types:
 *   1. Job completions — summarized and forwarded to Telegram
 *   2. Relay questions — mid-job questions forwarded to Telegram for user reply
 *
 * Usage:
 *   bun ./channels/artemis-webhook/index.ts
 *
 * Registered in .mcp.json so Claude Code spawns it automatically.
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const PORT = parseInt(process.env.ARTEMIS_WEBHOOK_PORT || "8790", 10);

const mcp = new Server(
  { name: "artemis-webhook", version: "0.1.0" },
  {
    capabilities: {
      experimental: { "claude/channel": {} },
    },
    instructions: [
      "## Job Completion Events",
      "",
      'Events from the artemis-webhook channel arrive as <channel source="artemis-webhook" ...>.',
      "These are notifications from the Artemis scheduler about completed recurring jobs.",
      "The event payload may also include an 'output' field with the tail of the job's terminal output.",
      "",
      "When you receive a job completion event:",
      "1. If 'output' is present, read it to understand what the job did and any questions it ended with.",
      '2. Check Supabase for any engagement_log entries with status "drafted" that need user approval.',
      "3. Check for upcoming interviews in the next 7 days (query jobs where status = 'interviewing').",
      "4. Check for blog_posts with status 'draft' or 'review' that are ready to publish.",
      "5. Format a concise summary of what the job did and any pending actions.",
      "6. Send the summary to the user via the Telegram reply tool so they see it on their phone.",
      "   - If the job output ends with a question or asks the user to do something, include it verbatim.",
      "   - If the job failed, include the error and suggest next steps.",
      "",
      "Keep the summary brief — the user is reading this on mobile. Use numbered lists for actionable items.",
      "If there are engagement drafts pending approval, include the content preview and ask the user to approve or skip.",
      "",
      "## Relay Questions (Bidirectional)",
      "",
      "When you receive an event with type 'relay_question', a scheduled job needs user input RIGHT NOW.",
      "The subprocess is blocked waiting for a reply. Act immediately:",
      "",
      "1. The 'question' field contains what the job is asking. The 'token' field is the relay token.",
      "2. Send the question to the user via Telegram reply tool. Format:",
      "   [Job Name] needs your input:",
      "",
      "   {question}",
      "",
      "   Reply here and I will relay your answer back.",
      "",
      "3. IMPORTANT: When the user replies on Telegram, you MUST route their answer back by running:",
      '   curl -s -X POST http://localhost:8000/api/relay/reply -H "Content-Type: application/json" -d \'{"token": "<TOKEN>", "answer": "<USER_REPLY>"}\'',
      "   Replace <TOKEN> with the relay token from the event and <USER_REPLY> with the user's response.",
      "   Make sure to properly escape the user's reply text for JSON.",
      "4. After posting the reply, confirm to the user: 'Relayed your answer to the [job] job.'",
      "5. If multiple relay questions arrive, handle them in order. Each has a unique token.",
      "6. Relay questions time out after 5 minutes. If the user hasn't replied and you receive a",
      "   new completion event for that job, the question has expired — no need to relay.",
    ].join("\n"),
  }
);

// Connect to Claude Code over stdio
await mcp.connect(new StdioServerTransport());

// Start HTTP server to receive scheduler notifications
Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req: Request): Promise<Response> {
    if (req.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const body = await req.json();
      const { type, job, skill, status, error, output, question, token } = body as {
        type?: string;
        job?: string;
        skill?: string;
        status?: string;
        error?: string;
        output?: string;
        question?: string;
        token?: string;
      };

      if (type === "relay_question") {
        // Mid-job question from a subprocess — needs immediate user attention
        const content = [
          `Relay question from scheduled job "${job || "unknown"}" (skill: ${skill || "unknown"})`,
          `Token: ${token || "unknown"}`,
          `Question: ${question || "(no question provided)"}`,
        ].join("\n");

        await mcp.notification({
          method: "notifications/claude/channel",
          params: {
            content,
            meta: {
              type: "relay_question",
              job: job || "unknown",
              skill: skill || "unknown",
              token: token || "unknown",
            },
          },
        });
      } else {
        // Job completion notification
        let content = `Scheduled job "${job || "unknown"}" completed with status: ${status || "unknown"}`;
        if (error) {
          content += `\nError: ${error}`;
        }
        if (output) {
          content += `\n\nJob output (last 40 lines):\n${output}`;
        }

        await mcp.notification({
          method: "notifications/claude/channel",
          params: {
            content,
            meta: {
              job: job || "unknown",
              skill: skill || "unknown",
              status: status || "unknown",
            },
          },
        });
      }

      return new Response("ok");
    } catch (err) {
      const message = err instanceof Error ? err.message : "unknown error";
      return new Response(`Error: ${message}`, { status: 400 });
    }
  },
});

// Log to stderr so it doesn't interfere with stdio MCP transport
console.error(`[artemis-webhook] Listening on http://127.0.0.1:${PORT}`);
