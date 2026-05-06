# NetBox integration

NetBox is the source of truth for IP addresses, contacts (employees), and secrets (device passwords / API tokens). This skill uses two integration paths:

1. **`gen-ip-names-tsv.py`** — pulls IP→contact mappings to produce the `ip-names.tsv` file other reports consume.
2. **Secrets API** — pull device passwords on-demand (so we don't hardcode in scripts).

## NetBox setup expected

- NetBox 3.x or 4.x running (Docker compose recommended)
- `netbox_secrets` plugin installed (https://github.com/Onemind-Services-LLC/netbox-secrets)
- At least one user with admin role
- IP addresses imported (per-host)
- Contacts created (per employee, with assignment to dept group)
- Contact-assignments linking IPs to contacts (this is what `gen-ip-names-tsv.py` reads)
- Secrets imported (device passwords) — encrypted via NetBox PEM master key

## Authentication

NetBox API has 2 paths:
- **Token auth** (`Authorization: Token <token>`) for most operations
- **Session cookie** for the secrets plugin (must come via web login)

For secrets decryption you also need:
- The user's **private PEM key** (from "User Profile → API Tokens → secrets keys" in NetBox UI)
- Server-issued **session-key** obtained by POSTing the PEM to `/api/plugins/secrets/session-keys/`

This skill uses **session cookie auth** for everything for simplicity (one auth path, no token rotation hassle).

### Sample auth flow (bash)

```bash
NB=http://10.0.0.204:8006
USER=admin
PASS=YOUR_PASSWORD  # store in env / NetBox secret / Vault, not in scripts
PK=/path/to/your-netbox-private-key.pem  # chmod 600

CJ=$(mktemp)

# 1. login
curl -sk -c $CJ "$NB/login/" >/dev/null
CSRF=$(grep csrftoken $CJ | awk '{print $NF}')
curl -sk -b $CJ -c $CJ -X POST "$NB/login/" \
    -H "Referer: $NB/login/" \
    -d "csrfmiddlewaretoken=$CSRF&username=$USER&password=$PASS&next=/" \
    -o /dev/null

# 2. get session-key for secrets decryption
CSRF=$(grep csrftoken $CJ | awk '{print $NF}')
SK=$(curl -sk -b $CJ -H "X-CSRFToken: $CSRF" -H "Referer: $NB" \
    -X POST --form "private_key=<$PK" \
    "$NB/api/plugins/secrets/session-keys/" \
    | jq -r '.session_key')

# 3. fetch + decrypt a secret
SECRET_ID=14
PLAINTEXT=$(curl -sk -b $CJ -H "X-Session-Key: $SK" \
    "$NB/api/plugins/secrets/secrets/$SECRET_ID/" \
    | jq -r '.plaintext')
```

## `gen-ip-names-tsv.py`

Generates `/opt/mis-log-db/ip-names.tsv` (tab-separated `IP\tName`) from three sources, in priority order (later wins):

1. **FG DHCP `reserved-address` description** — fallback for hosts not in NetBox
2. **NetBox** — primary; pulls all IPs + their assigned contact name (priority=primary)
3. **Manual override** (`ip-names-manual.tsv`) — for infra labels (FortiGate / switches / NAS / printers) that don't fit the "employee" model

### Manual override format

```
# Manual overrides for ip-names.tsv (run via gen-ip-names-tsv.py)
# Format: <IP>\t<Name>  (tab-separated, # comments OK, blank lines ignored)

10.0.0.1	FortiGate
10.0.0.14	QNAP NAS
10.0.0.31	HP Switch (5F)
10.0.0.200	MIS hub server
10.0.0.204	NetBox / LibreNMS
10.0.0.206	AD DC + ERP / Hyper-V host
```

### Schedule

```
2 * * * * root /usr/bin/python3 /opt/mis-log-db/gen-ip-names-tsv.py >> /var/log/mis-gen-ip-names.log 2>&1
```

Hourly is fine — IP/contact assignments don't change often. After making a NetBox edit, you can manually trigger:

```bash
sudo /opt/mis-log-db/gen-ip-names-tsv.py
```

## NetBox URL / auth in scripts

Look at the top of `gen-ip-names-tsv.py` for the constants:

```python
NB_URL    = 'http://10.0.0.204:8006'
NB_USER   = 'admin'
NB_PASS   = 'CHANGE_ME'
```

**Don't commit a real password!** Recommend pulling from env:

```python
import os
NB_PASS = os.environ.get('NETBOX_PASSWORD') or sys.exit('Set NETBOX_PASSWORD env var')
```

Then run:
```bash
sudo NETBOX_PASSWORD=secret /opt/mis-log-db/gen-ip-names-tsv.py
```

Or via systemd EnvironmentFile / cron `MAILTO=user; ENV=...` line.

## Reading employee data from NetBox

Useful API patterns the scripts use:

### List all contact groups (departments)

```bash
curl -sk -b $CJ "$NB/api/tenancy/contact-groups/" \
    | jq '.results[] | "\(.id) \(.name)"'
```

### List contacts in a group

```bash
GROUP_ID=6
curl -sk -b $CJ "$NB/api/tenancy/contacts/?group_id=$GROUP_ID&limit=20" \
    | jq '.results[] | "\(.id) \(.name) [\(.title)]"'
```

### Find IP assignment for a contact

```bash
CONTACT_ID=58
curl -sk -b $CJ "$NB/api/tenancy/contact-assignments/?contact_id=$CONTACT_ID" \
    | jq '.results[] | select(.object_type=="ipam.ipaddress") | .object_id'
# returns the IP-id; then GET /api/ipam/ip-addresses/<id>/ for the IP
```

### Search secrets by device IP

```bash
IP_ID=28
curl -sk -b $CJ "$NB/api/plugins/secrets/secrets/?assigned_object_id=$IP_ID" \
    | jq '.results[] | "\(.id) \(.name) [\(.role.name)]"'
```

## Privacy

- **PEM private key**: never commit to repo. Store in OS keychain (`security` on macOS, `secret-tool` on Linux). Backup separately (encrypted USB / printed QR).
- **NetBox admin password**: rotate quarterly. Use env vars not hardcoded constants.
- **Lost PEM = all encrypted secrets unrecoverable** — multiple backups essential.
