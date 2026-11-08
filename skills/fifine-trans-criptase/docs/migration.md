# Migration to the skill CLI

The MCP server has been removed. Invoke the installed skill or run `node scripts/semantic.mjs` for its local commands. Existing `config/config.json` and legacy `embed-config.json` remain readable, and indexes are not deleted. Old client-side MCP registrations are not modified by installation; remove stale registrations from the client if they still point to the removed server. See `environment.md` for private configuration and `../README.md` for usage.
