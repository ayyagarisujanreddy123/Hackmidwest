# AWS Demo Deployment

**Prepared; provisioning approval pending.** The owner selected EC2 with a temporary Cloudflare HTTPS tunnel. The working Mac MCP, synthetic API, approval database, and DevRev connection remain the fallback. No EC2 instance, role, or public endpoint has been created. AWS hosting does not establish Akamai-track eligibility.

## Verified preflight and proposed resources

Read-only AWS CloudShell checks on October 11, 2026 UTC confirmed an active Free Plan with **$120** remaining credits, expiring April 10, 2027. Ohio has no existing active/stopped instances or instance profiles. `t3.small` and the latest Canonical Ubuntu 24.04 x86-64 image are marked Free Tier eligible. An EC2 launch **DryRun** returned `DryRunOperation`; it created nothing and does not prove capacity or new-role permissions.

Provision only after explicit owner approval:

- One `t3.small` in `us-east-2`: 2 vCPU, 2 GiB RAM, Ubuntu 24.04, **standard** CPU credits, encrypted 8 GiB gp3 root disk, and IMDSv2 required. Use the verified default VPC/subnet; no new VPC, NAT, database, load balancer, or Elastic IP.
- One security group: SSH from Ohio's AWS-managed EC2 Instance Connect prefix list; temporarily allow the current CloudShell IPv4 `/32` for private artifact transfer, then remove that rule. No public ingress to ports 8000, 8001, or 8002. Outbound access supports packages, Bedrock, and Cloudflare.
- One EC2 role/profile `contextforge-ec2-demo` with the [EC2 trust policy](ec2-trust-policy.json) and [restricted Nova policy](nova-micro-policy.json.example). Substitute the actual account ID after approval. This grants catalog reads in Ohio and inference through **only** `us.amazon.nova-micro-v1:0`; its verified model destinations are Ohio, Northern Virginia, and Oregon. No IAM administration, source-service privileges, permanent keys, or account upgrade.
- The existing MCP/source/Strands code; private state at `/var/lib/contextforge`, historical approval archive at `/var/lib/contextforge-archive`, and receipts at `/opt/contextforge/validation_logs`.

[Instance profiles](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html), [profile permissions](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html), [SSH restrictions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-prerequisites.html).

## Cost and shutdown proposal

AWS Price List queries returned these **Ohio** rates:

| Item | Verified rate | Approximate 24-hour cost |
|---|---|---|
| Linux `t3.small` | $0.0208/hour | $0.4992 |
| 8 GiB gp3, baseline IOPS/throughput | $0.08/GiB-month | $0.021 |
| Auto-assigned public IPv4 | $0.005/hour | $0.12 |
| Nova Micro on-demand | $0.000035/1K input; $0.00014/1K output tokens | Based on actual usage |

VM/storage/IP total is approximately **$0.64/day**, before model calls and transfer. For example, 100,000 input plus 20,000 output tokens costs $0.0063. Propose **24 hours**, at most 20 bounded generation/readiness runs, and a **$5 credit-consumption ceiling**. These limits are not yet authorized and are not an AWS billing hard cap. Recheck credits before launch; stop new runs if consumption approaches the ceiling.

The deployment operator schedules an OS shutdown for the end of the approved window and verifies EC2's instance-initiated shutdown behavior is `stop`. Stopping releases the auto-assigned IPv4 but retains the encrypted disk, which continues to cost approximately $0.64/month. Keep evidence; ask separately before final termination/deletion. Do not extend runtime without approval. [IPv4 pricing](https://aws.amazon.com/vpc/pricing/), [EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/).

## Package and install independently

Build a **private** bundle from the current reviewed working tree:

```zsh
contextforge_mcp_starter/.venv/bin/python deploy/build_bundle.py build \
  --registry contextforge_mcp_starter/state/capabilities.sqlite3 \
  --output /private/tmp/contextforge-ec2-demo.tar.gz
```

The explicit file allowlist excludes `.venv`, `.aws`, token files, approval policies, and local environment files. SQLite's backup API preserves every original approval record unchanged in a separate archive. It also exports the exact approved manifest and source hash. The bundle and extracted files start with mode 600; never commit or publicly upload this archive.

After infrastructure approval, privately transfer the bundle and reviewed extraction helper to the EC2 host. Verify the helper's reviewed hash, then verify the bundle's saved SHA-256 before extraction:

```bash
sudo python3 build_bundle.py extract contextforge-ec2-demo.tar.gz \
  --sha256 REVIEWED_BUNDLE_SHA256 --destination /opt/contextforge
sudo bash /opt/contextforge/deploy/install_ec2.sh
```

The installer refuses existing state/accounts/services, installs a fresh pinned Linux environment and Cloudflare's signed vendor package, archives the original database, and starts only the loopback synthetic API. It does **not** register an administrator, approve a connector, or start MCP/the public tunnel. Actual Linux installation/systemd startup remain NOT TESTED until deployment.

The account owner privately enters the **existing** server token into root-owned `/etc/contextforge/mcp.env` (mode 600). Never paste it into chat, command arguments, userdata, or logs. Only the MCP unit receives this file. `/etc/contextforge/source.env` contains non-secret configuration and deliberately omits `AWS_PROFILE`; the SDK obtains temporary credentials from the approved EC2 role.

## Validate and retain human approval

Run administrative CLI commands as the registry owner, using the non-secret environment:

```bash
sudo -H -u contextforge bash -c 'set -a; source /etc/contextforge/source.env; set +a; cd /opt/contextforge/contextforge_mcp_starter; exec .venv/bin/python strands_workflow.py check-bedrock --region us-east-2'
sudo -H -u contextforge bash -c 'set -a; source /etc/contextforge/source.env; set +a; cd /opt/contextforge; exec contextforge_mcp_starter/.venv/bin/python deploy/validate_migration.py'
```

Require actual inference plus a Strands tool/result call, all ten real manifest/API checks, the unchanged capability ID, and `approval_required` on attempted execution. The original Mac approval binds to UID 501 and stays in the archive. **Do not edit or impersonate that UID.** An authorized human must interactively run the existing `init-admin` and `approve <tested-id>` CLI as the new registry owner, reviewing the exact manifest/source/validation report and typing both confirmations themselves. No agent or startup unit can approve.

Then start MCP, test its authenticated/unauthorized loopback requests, and start `contextforge-tunnel.service`. The tunnel points only to MCP port 8000, preserves the existing Host allowlist, receives no bearer environment file, and uses info-level logs. Record the actual `https://…trycloudflare.com/mcp` URL. A tunnel-process restart changes this hostname; MCP-only restarts can preserve it. Quick Tunnels have no uptime guarantee or SSE support; this server already uses JSON Streamable HTTP. [Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Hosted acceptance and cutover

Before touching the existing DevRev connection, execute and record:

1. Role-based Bedrock/Strands readiness and actual missing-capability proposal/validation on the approved synthetic API; retain candidate inactivity until human approval.
2. HTTPS MCP initialize/discovery, both original tools, missing/wrong-token 401, and approved `RunCapability` for DEMO-101 and DEMO-102 with real GET receipts/source references. DEMO-403 must remain HTTP 403 without records.
3. MCP/source service restart with approval, registry, and evidence persistence. Keep the tunnel running during this check; verify no public source/demo port is reachable.
4. Supply the verified AWS tunnel URL for a **new staged** DevRev connection; execute real Computer calls and teammate reuse there before replacing the local connector.

Stop on AWS permission/Free Plan/model errors and report the exact sanitized error. Do not widen IAM, upgrade the account, remove the local database, or claim hosted PASS from local/static tests. Preserve the original endpoint as rollback until hosted Computer calls pass.
