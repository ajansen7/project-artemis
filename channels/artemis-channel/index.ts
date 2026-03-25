#!/usr/bin/env bun
/**
 * Artemis Channel — push-based event bridge between the FastAPI backend
 * and the running Claude orchestrator session.
 *
 * The API POSTs here after inserting into task_queue. This channel
 * immediately pushes the event into Claude's context so tasks are
 * picked up in milliseconds instead of up to 30 seconds.
 *
 * Event types:
 *   POST /task   — a new task was queued (from any API route)
 *   POST /notify — generic notification (schedule fired, etc.)
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const PORT = parseInt(process.env.ARTEMIS_CHANNEL_PORT || "8790", 10);

const mcp = new Server(
  { name: "artemis-channel", version: "1.0.0" },
  {
    capabilities: {
      experimental: { "claude/channel": {} },
    },
    instructions: [
      "## Artemis Task Channel",
      "",
      'When you receive a <channel source="artemis-channel" type="task"> event, a new skill task',
      "has been queued and is waiting for you to execute it. Act immediately:",
      "",
      "1. Parse the task from the event content (JSON with id, skill, skill_args, name, source).",
      "2. Execute the skill using the Skill tool: invoke the skill named in the 'skill' field,",
      "   passing 'skill_args' as the argument if present.",
      "3. When done, update the task status:",
      "   uv run python .claude/tools/db.py update-task --id <id> --status complete --output-summary '<brief summary>'",
      "   On failure: uv run python .claude/tools/db.py update-task --id <id> --status failed --error '<reason>'",
      "4. Send a brief Telegram summary:",
      "   uv run python .claude/tools/push_to_telegram.py summary --job-name '<task name>' --status success --body '<summary>'",
      "",
      "If the skill_args contain a job ID or target, pass it along. Keep execution focused — do not",
      "ask clarifying questions unless the task genuinely requires user input.",
      "",
      'For <channel source="artemis-channel" type="notify"> events, read the content and take',
      "any indicated action (e.g. schedule fired, approval needed).",
    ].join("\n"),
  }
);

await mcp.connect(new StdioServerTransport());

Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);

    if (req.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    let body: Record<string, unknown>;
    try {
      body = await req.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    if (url.pathname === "/task") {
      // New task queued — push into Claude immediately
      const { id, name, skill, skill_args, source } = body as {
        id?: string;
        name?: string;
        skill?: string;
        skill_args?: string | null;
        source?: string;
      };

      const content = JSON.stringify({ id, name, skill, skill_args, source });

      await mcp.notification({
        method: "notifications/claude/channel",
        params: {
          content,
          meta: {
            type: "task",
            id: String(id ?? ""),
            skill: String(skill ?? ""),
            source: String(source ?? "api"),
          },
        },
      });

      console.error(`[artemis-channel] Task pushed: ${name} (${skill})`);
      return new Response("ok");
    }

    if (url.pathname === "/notify") {
      // Generic notification
      const { message, context } = body as {
        message?: string;
        context?: string;
      };

      await mcp.notification({
        method: "notifications/claude/channel",
        params: {
          content: message ?? "(no message)",
          meta: {
            type: "notify",
            context: String(context ?? ""),
          },
        },
      });

      console.error(`[artemis-channel] Notification pushed: ${message}`);
      return new Response("ok");
    }

    return new Response("Not found", { status: 404 });
  },
});

console.error(`[artemis-channel] Listening on http://127.0.0.1:${PORT}`);
