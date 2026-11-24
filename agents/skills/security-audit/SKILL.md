---
name: security-audit
description: Static code security, credential hygiene, and prompt injection defense.
---

# Security Audit Skill (NEURON.ONE GodMode Edition)

## Objective
Enforce strict security standards across all DAZY runtime components:
1. **Zero Hardcoded Secrets**: All API keys, tokens, and credentials must live exclusively in `config/api_keys.json` or `appinfo11.txt`. Never commit plaintext secrets to Git.
2. **Access Control**: Restrict sensitive local OS commands (e.g., file deletion, shell execution) behind PIN authentication (default: `786786`) or explicit user confirmation.
3. **Prompt Injection Defense**: Sanitize user inputs and external tool outputs before feeding them into LLM prompt templates. Guard against system prompt override attacks.
4. **Rate Limit & Egress Defense**: Guard against token quota exhaustion with automatic prompt budget capping.
