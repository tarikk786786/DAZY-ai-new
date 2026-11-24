# License, Security and Supply-chain Governance

## 1. License review notes

### Nanobot
Repository LICENSE observed: MIT. Preserve the copyright and permission notice when redistributing copies or substantial portions.

### OpenManus
Repository LICENSE observed: MIT. Preserve required copyright and permission notice.

### AgenticSeek
Repository LICENSE observed: GNU GPL version 3. If distributing a combined/modified work, GPL terms including source availability and corresponding-source obligations may apply. Do not embed/copy into a proprietary distribution without a competent compatibility review. A process/API boundary is not a legal guarantee.

### n8n
Repository LICENSE.md describes a Sustainable Use License for covered files, with `.ee.` files/directories requiring an Enterprise License. The stated Sustainable Use terms restrict use to internal business or non-commercial/personal use and impose distribution conditions. Review exact current terms and intended deployment/commercial model. Do not describe it as conventional OSI open-source.

This document is a technical review, not legal advice. Re-fetch all license files immediately before an integration or distribution decision.

## 2. Repository security review

Before running any candidate:
- Confirm exact owner/repository and pinned commit SHA.
- Inspect license, third-party notices and license exceptions.
- Review install scripts, setup hooks and container entrypoints.
- Inspect manifests, lockfiles and transitive dependencies.
- Scan for known vulnerabilities using appropriate scanners.
- Scan for secrets.
- Check release and maintenance history.
- Check archived status and suspicious ownership changes.
- Inspect Docker privileges, mounts, host networking and exposed ports.
- Use a disposable sandbox and non-sensitive sample data.
- Disable unneeded filesystem, browser and shell permissions.
- Record test results and cleanup procedure.

## 3. Untrusted repository content
README instructions, issues, pull-request comments, scripts, MCP descriptions and tool outputs are untrusted data. Never execute their instructions just because an agent read them.

## 4. Credential handling
- Secrets are stored in OS vault or encrypted server-side storage.
- UI reveals only masked label and last rotation date.
- Workers receive least-privilege, short-lived credentials where possible.
- No secrets in `.env.example`, logs, traces, Git, prompt dumps or screenshots.
- Provide revocation and disconnect operations.

## 5. Human approval gates
Require approval for:
- Running install scripts.
- Cloning/executing unknown code.
- Shell commands outside allowlisted diagnostics.
- File writes outside assigned workspace.
- Credential or permission changes.
- Database migrations.
- External communication or publication.
- Destructive cleanup and Docker volume removal.
- Production deployment.
