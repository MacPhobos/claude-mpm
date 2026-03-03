# Agent Templates Archive (Reference Only)

This directory contains 39 JSON agent definition files preserved as a
canonical reference for rich agent metadata. These files are NOT read
by any production code at runtime.

## Purpose
- Reference for agent capabilities, interactions, memory_routing, and skill mappings
- Source material for the `delegation_matrix_poc.py` script
- Historical record of the original JSON template schema

## NOT Used By
- AgentTemplateBuilder (reads from git cache, not archive)
- SkillManager (path bug: scans `templates/*.json`, not `templates/archive/*.json`)
- Any runtime production code path

## Field Convention
All 39 JSON files use `"agent_type"` as the field name (not `"type"`).
