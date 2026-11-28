#!/usr/bin/env bash
# Run on zion2test as root. Persist only the existing RealmProof relay exception.
set -euo pipefail

if (( EUID != 0 )); then
  echo 'Run this installer as root.' >&2
  exit 1
fi

install -d -m 0755 /usr/local/libexec
install -m 0755 /dev/stdin /usr/local/libexec/realmproof-onyx-firewall <<'RULE'
#!/usr/bin/env bash
set -euo pipefail

network=ln-studio-a3001f8f92554e758bcdac87e2a093e5
subnet=10.0.9.0/24
gateway=10.0.9.1
tag=realmproof-onyx-relay
# Prevent overlap between a manual invocation and the timer.
exec 9>/run/lock/realmproof-onyx-firewall.lock
flock -w 10 9

read -r network_id driver internal < <(
  docker network inspect "$network" --format '{{.Id}} {{.Driver}} {{.Internal}}'
)
[[ "$driver" == bridge && "$internal" == false && "$network_id" =~ ^[a-f0-9]{64}$ ]]
docker network inspect "$network" \
  --format '{{range .IPAM.Config}}{{println .Subnet .Gateway}}{{end}}' |
  grep -Fxq "$subnet $gateway"

bridge=$(docker network inspect "$network" \
  --format '{{with index .Options "com.docker.network.bridge.name"}}{{.}}{{end}}')
bridge=${bridge:-br-${network_id:0:12}}
ip -4 -o addr show dev "$bridge" | awk '{print $4}' | grep -Fxq "$gateway/24"

match=(-i "$bridge" -s "$subnet" -d "$gateway/32" -p tcp --dport 8765)
rule=("${match[@]}" -j ACCEPT)
managed=("${match[@]}" -m comment --comment "$tag" -j ACCEPT)
first=$(iptables -w -S INPUT 1 2>/dev/null || true)
first=${first//\"/}
if [[ " $first " != *" --comment $tag "* ]] ||
   ! iptables -w -C INPUT "${managed[@]}" 2>/dev/null; then
  if iptables -w -C INPUT "${managed[@]}" 2>/dev/null; then
    iptables -w -D INPUT "${managed[@]}"
  fi
  iptables -w -I INPUT 1 "${managed[@]}"
fi
# Retire the exact temporary rule after the managed rule is installed.
if iptables -w -C INPUT "${rule[@]}" 2>/dev/null; then
  iptables -w -D INPUT "${rule[@]}"
fi
RULE

cat > /etc/systemd/system/realmproof-onyx-firewall.service <<'UNIT'
[Unit]
Description=Allow only the RealmProof bridge to reach the private Onyx relay
After=docker.service ufw.service
Wants=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/libexec/realmproof-onyx-firewall
UNIT

cat > /etc/systemd/system/realmproof-onyx-firewall.timer <<'UNIT'
[Unit]
Description=Restore the RealmProof relay firewall exception after rule reloads

[Timer]
OnBootSec=15s
OnUnitActiveSec=30s
AccuracySec=5s

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl start realmproof-onyx-firewall.service
systemctl enable --now realmproof-onyx-firewall.timer
systemctl is-active realmproof-onyx-firewall.timer
