#!/usr/bin/env bash
# Run only on the approved fresh Ubuntu host after verifying/extracting the bundle.
set -euo pipefail
umask 077

if [[ $EUID -ne 0 ]]; then
    printf '%s\n' 'Run this installer as root on the approved EC2 host.' >&2
    exit 1
fi
source /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 24.04 || "$(uname -m)" != x86_64 ]]; then
    printf '%s\n' 'This deployment supports Ubuntu 24.04 x86-64 only.' >&2
    exit 1
fi
cd /opt/contextforge
if [[ ! -f bundle-manifest.json || ! -f migration/legacy-registry.sqlite3 ]]; then
    printf '%s\n' 'Verified deployment bundle and approval archive are required.' >&2
    exit 1
fi
if [[ -e /var/lib/contextforge || -e /var/lib/contextforge-archive || -e /etc/contextforge ]] || getent passwd contextforge >/dev/null; then
    printf '%s\n' 'Refusing to overwrite an existing service account or registry.' >&2
    exit 1
fi
for unit in source mcp tunnel; do
    if [[ -e "/etc/systemd/system/contextforge-$unit.service" ]]; then
        printf '%s\n' 'Refusing to overwrite an existing ContextForge service.' >&2
        exit 1
    fi
done

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv curl ca-certificates
install -d -m 0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
chmod 0644 /usr/share/keyrings/cloudflare-main.gpg
printf '%s\n' 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared noble main' > /etc/apt/sources.list.d/cloudflared.list
chmod 0644 /etc/apt/sources.list.d/cloudflared.list
apt-get update
apt-get install -y cloudflared

useradd --system --create-home --home-dir /var/lib/contextforge --shell /usr/sbin/nologin contextforge
chmod 0700 /var/lib/contextforge
install -d -o root -g root -m 0700 /var/lib/contextforge-archive
mv migration/legacy-registry.sqlite3 /var/lib/contextforge-archive/legacy-registry.sqlite3
chmod 0400 /var/lib/contextforge-archive/legacy-registry.sqlite3
chown -R root:root /opt/contextforge
chmod -R u=rwX,go=rX /opt/contextforge
python3 -m venv contextforge_mcp_starter/.venv
contextforge_mcp_starter/.venv/bin/python -m pip install -r contextforge_mcp_starter/requirements-workflow.txt
contextforge_mcp_starter/.venv/bin/python -m pip check

install -d -o contextforge -g contextforge -m 0700 /opt/contextforge/validation_logs
install -d -o root -g contextforge -m 0750 /etc/contextforge
install -m 0644 deploy/source.env.example /etc/contextforge/source.env
for unit in source mcp tunnel; do
    install -m 0644 "deploy/contextforge-$unit.service.example" "/etc/systemd/system/contextforge-$unit.service"
done
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/contextforge-{source,mcp,tunnel}.service
systemctl enable --now contextforge-source.service
printf '%s\n' 'Source installed. MCP and tunnel are NOT started.' 'Next: private token entry, AWS readiness, real validation, and interactive human approval.'
