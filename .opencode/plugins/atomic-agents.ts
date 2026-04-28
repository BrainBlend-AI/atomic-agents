import type { Plugin } from "@opencode-ai/plugin"

export default (async (_ctx) => {
  return {
    "shell.env": async (_input, output) => {
      output.env.UV_PROJECT_ENVIRONMENT = ".venv"
    },
  }
}) satisfies Plugin
