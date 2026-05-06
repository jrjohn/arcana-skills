# AD LDAP queries from Linux

Querying Microsoft Active Directory from a CentOS hub via `ldapsearch`. Useful for: discovering AD usernames, finding which computer a user last logged into, auditing stale accounts, mapping `samAccountName` ↔ employee number.

## Setup

### Install client

```bash
sudo dnf install -y openldap-clients   # provides ldapsearch
```

### Test reachability

```bash
nc -zv <AD_IP> 389        # plain LDAP (read-only safe over LAN)
nc -zv <AD_IP> 636        # LDAPS (TLS-wrapped)
```

## The base DN trap

The biggest gotcha: **AD base DN ≠ DNS domain**.

| You think | Reality |
|---|---|
| Domain is `arcana.com.tw` (per email / DNS) | AD forest root is `arcana.com` (different!) |
| → so base DN must be `dc=arcana,dc=com,dc=tw` | → actual base DN is `DC=arcana,DC=com` |

Always discover the real base DN first via anonymous LDAP query:

```bash
ldapsearch -x -H ldap://<AD_IP> -s base -b '' '(objectClass=*)' defaultNamingContext
# returns: defaultNamingContext: DC=arcana,DC=com
```

Use that exact value for `-b` in subsequent queries.

## Authentication

For anything beyond `defaultNamingContext`, AD requires bind:

```bash
ldapsearch -x -LLL -H ldap://<AD_IP> \
    -D 'administrator@arcana.com' \
    -w 'YOUR_PASSWORD' \
    -b 'DC=arcana,DC=com' \
    '<filter>' [<attributes>...]
```

`-D` is the bind DN (use UPN form `user@domain`, not `cn=...,dc=...`).
`-w 'PASSWORD'` for inline (insecure — use `-y file` for production).

Recommended: pull password from NetBox at run time:

```bash
PASS=$(curl -sk -b $CJ -H "X-Session-Key: $SK" \
    "$NB/api/plugins/secrets/secrets/14/" | jq -r .plaintext)

ldapsearch ... -w "$PASS" ...
```

## Common queries

### Find a user account

```bash
ldapsearch -x -LLL -H ldap://<AD_IP> -D 'admin@arcana.com' -w "$PASS" \
    -b 'DC=arcana,DC=com' \
    '(sAMAccountName=jdoe)' \
    sAMAccountName displayName description userAccountControl lastLogonTimestamp
```

### Find users matching multiple criteria (OR)

```bash
ldapsearch ... '(|(sAMAccountName=jdoe)(sAMAccountName=jsmith)(displayName=*Smith*))'
```

### List all enabled user accounts

```bash
# userAccountControl bit 0x2 = ACCOUNTDISABLE; UAC=512 = enabled, 514 = disabled
ldapsearch ... '(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))' \
    sAMAccountName displayName
```

### List all computer objects

```bash
ldapsearch ... '(objectClass=computer)' \
    name dNSHostName operatingSystem lastLogonTimestamp managedBy
```

### Find ex-employee accounts still enabled

```bash
ldapsearch ... '(sAMAccountName=ex.employee)' userAccountControl lastLogonTimestamp
```

Decode `userAccountControl`:
| Value | Meaning |
|---|---|
| 512 | Normal account, enabled |
| 514 | Normal account, disabled |
| 66048 | Normal account + DONT_EXPIRE_PASSWORD (UAC=0x10200) |
| 66050 | Normal + DONT_EXPIRE + DISABLED |

## `lastLogonTimestamp` interpretation

AD stores this as Windows FILETIME (100-ns intervals since 1601-01-01). To convert:

```bash
TS=132913498380618533    # raw value from AD
# Subtract 1601→1970 epoch offset (11644473600 sec), divide by 10000000 (100ns→s)
EPOCH=$(echo "($TS - 11644473600 * 10000000) / 10000000" | bc)
date -d "@$EPOCH"
# e.g.: Wed May 5 11:04:10 UTC 2026
```

**Important caveat**: AD only updates `lastLogonTimestamp` every 9-14 days for replication efficiency. So "lastLogon = today" might actually mean "logged in within the last 2 weeks". Don't use for fine-grained timing.

## Mapping employee data

Common mapping you'll need: `samAccountName` ↔ `employeeID` (a custom attribute or just embedded in `sAMAccountName` like `e1234`) ↔ `displayName` ↔ assigned computer.

```bash
# Find computer last-logged-into by a user
USER=jdoe
ldapsearch ... '(objectClass=computer)' name dNSHostName lastLogonTimestamp \
    | awk '/^name:/{n=$2} /^dNSHostName:/{h=$2} /^lastLogonTimestamp:/{print n,h,$2}' \
    | sort -k3 -rn | head -10
```

(Find computers with most recent lastLogon — but doesn't tell you WHICH user. AD doesn't track user-on-computer in standard schema; need event log scrape for that.)

## Listing all sAMAccountNames (cheap way)

```bash
ldapsearch ... '(&(objectCategory=person)(objectClass=user))' sAMAccountName \
    | grep '^sAMAccountName:' | awk '{print $2}' | sort
```

Useful when employee list is incomplete and you need to discover format conventions used in the org (e.g. `firstname.lastname` vs `e<empID>` vs `<chinesepinyin>`).

## Common pitfalls

1. **Anonymous binds disabled by default** on AD. You'll get `Operations error` on most queries without `-D ... -w ...`.
2. **Service account permissions**: don't use Domain Admin for read-only queries — create a dedicated `ldap-readonly` user with read access to specific OUs.
3. **TLS chain**: if using LDAPS (`-H ldaps://...`), the AD's self-signed cert won't validate by default. Either trust the CA or use `-o tls_reqcert=allow`.
4. **Encoded values**: some attributes return as base64 (`displayName::` instead of `displayName:`). Decode with `base64 -d`.
5. **Pagination**: AD limits results to 1000 per query. For larger sets, use `-E pr=500` (paged results) or filter narrower.

## When to use this vs. PowerShell on AD itself

| Use case | Tool |
|---|---|
| One-off lookup from Linux | `ldapsearch` (this module) |
| Bulk operations / modify users | PowerShell `Get-ADUser` / `Set-ADUser` on the DC |
| Cron monitoring (e.g. detect stale accounts) | `ldapsearch` from hub |
| Real-time change subscription | LDAP control `1.2.840.113556.1.4.528` (rare) |

For most MIS audit work, `ldapsearch` from the hub is sufficient — and avoids needing to RDP into the AD DC.
