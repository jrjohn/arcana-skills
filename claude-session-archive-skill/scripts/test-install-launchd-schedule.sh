#!/bin/bash
# Tests for install-launchd-schedule.sh + crs-build-launcher.
# Every scenario runs in a scratch HOME with a FAKE launchctl, so nothing here can
# touch the real launchd domain, the real plist, or the real env.sh.
#
#   bash scripts/test-install-launchd-schedule.sh
#
# Each scenario is a way this install has actually broken, or would have.
set -uo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HELPER="$SKILL_DIR/scripts/install-launchd-schedule.sh"
PB=/usr/libexec/PlistBuddy
U="$(id -un)"
pass=0; fail=0
ok()  { echo "    ✅ $1"; pass=$((pass + 1)); }
bad() { echo "    ❌ $1"; fail=$((fail + 1)); }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

new_sandbox() {
  SB="$(mktemp -d)"
  mkdir -p "$SB/bin" "$SB/home/Library/LaunchAgents" "$SB/home/.config/crs"
  export FAKE_LOG="$SB/launchctl.log" FAKE_STATE="$SB/loaded" FAKE_FAIL="$SB/fail_left"
  cat > "$SB/bin/launchctl" <<'EOF'
#!/bin/bash
echo "$*" >> "$FAKE_LOG"
case "$1" in
  list)
    # Loaded label FIRST, then plenty more lines: a `| grep -q` reader would stop
    # early and SIGPIPE the writer — the pipefail false-negative this guards against.
    [ -f "$FAKE_STATE" ] && printf '123\t0\t%s\n' "$(cat "$FAKE_STATE")"
    for i in $(seq 1 3000); do printf -- '-\t0\tcom.apple.filler.%s\n' "$i"; done ;;
  bootstrap)
    if [ -f "$FAKE_FAIL" ] && [ "$(cat "$FAKE_FAIL")" -gt 0 ]; then
      echo $(( $(cat "$FAKE_FAIL") - 1 )) > "$FAKE_FAIL"; exit 5
    fi
    basename "$3" .plist > "$FAKE_STATE" ;;
  bootout) rm -f "$FAKE_STATE" ;;
esac
exit 0
EOF
  chmod +x "$SB/bin/launchctl"
  PLIST="$SB/home/Library/LaunchAgents/com.$U.claude-archive.plist"
  ENV_SH="$SB/home/.config/crs/env.sh"
  LAUNCHER="$SB/home/claude-archive/bin/crs-build-launcher"
}
run_helper() {   # $1 = WITH_PG
  HOME="$SB/home" LAUNCHCTL="$SB/bin/launchctl" bash "$HELPER" "$SKILL_DIR" "$1" > "$SB/out.txt" 2>&1
}
old_plist() {    # $1 = host, $2 = password  (the pre-fix inline-credential style)
  # XML-escape like any real plist writer would. The first version of this test
  # wrote a raw '&', producing a file PlistBuddy cannot read — which is how the
  # helper's "error text taken as the password" bug surfaced (scenario 7).
  local pw; pw="$(printf '%s' "$2" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')"
  set -- "$1" "$pw"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.$U.claude-archive</string>
  <key>ProgramArguments</key><array><string>$SB/home/claude-archive/crs/target/release/crs</string><string>build</string></array>
  <key>EnvironmentVariables</key><dict>
    <key>CRS_PG_HOST</key><string>$1</string>
    <key>CRS_PG_PORT</key><string>5432</string>
    <key>CRS_PG_PASSWORD</key><string>$2</string>
  </dict>
</dict></plist>
EOF
}
has_creds() { $PB -c "Print :EnvironmentVariables:CRS_PG_PASSWORD" "$PLIST" >/dev/null 2>&1; }
prog0()     { $PB -c "Print :ProgramArguments:0" "$PLIST" 2>/dev/null; }

echo "1) fresh install, --with-pg"
new_sandbox; run_helper 1; rc=$?
check "exit 0"                                  '[ $rc -eq 0 ]'
check "launcher installed + executable"          '[ -x "$LAUNCHER" ]'
check "plist runs the launcher"                  '[ "$(prog0)" = "$LAUNCHER" ]'
check "plist carries NO credentials"             '! has_creds'
check "env.sh created with placeholders, mode 600" 'grep -q REPLACE_WITH_YOUR_PG_PASSWORD "$ENV_SH" && [ "$(stat -f %Lp "$ENV_SH")" = 600 ]'
check "bootstrapped"                             'grep -q "^bootstrap" "$FAKE_LOG"'

echo "2) the 2026-07-23 case: re-run WITHOUT --with-pg on a PG install"
new_sandbox
printf 'export CRS_PG_HOST=real.host\nexport CRS_PG_PASSWORD=realpw\n' > "$ENV_SH"; chmod 600 "$ENV_SH"
before="$(shasum "$ENV_SH")"
old_plist "arcana.example.com" "REPLACE_WITH_YOUR_PG_PASSWORD"
run_helper 0
check "env.sh untouched (byte-identical)"         '[ "$(shasum "$ENV_SH")" = "$before" ]'
check "placeholder plist replaced by launcher"    '[ "$(prog0)" = "$LAUNCHER" ]'
check "no placeholder host left in plist"         '! grep -q arcana.example.com "$PLIST"'
check "old plist backed up"                        'ls "$PLIST".bak-* >/dev/null 2>&1'

echo "3) old plist with REAL inline credentials, no env.sh, re-run WITHOUT --with-pg"
new_sandbox
PW='p@ss w$rd'"'"'"&;x'
old_plist "db.real.example" "$PW"
run_helper 0
check "env.sh created from the old plist"         '[ -f "$ENV_SH" ]'
check "password migrated byte-for-byte"           '[ "$(bash -c ". \"$ENV_SH\"; printf %s \"\$CRS_PG_PASSWORD\"")" = "$PW" ]'
check "host migrated"                              '[ "$(bash -c ". \"$ENV_SH\"; printf %s \"\$CRS_PG_HOST\"")" = "db.real.example" ]'
check "env.sh mode 600"                            '[ "$(stat -f %Lp "$ENV_SH")" = 600 ]'
check "new plist carries NO credentials"           '! has_creds'

echo "4) re-run on an install that is already current and loaded"
new_sandbox; run_helper 1
sum_plist="$(shasum "$PLIST")"; sum_env="$(shasum "$ENV_SH")"
: > "$FAKE_LOG"
run_helper 1
check "plist unchanged"                            '[ "$(shasum "$PLIST")" = "$sum_plist" ]'
check "env.sh unchanged"                           '[ "$(shasum "$ENV_SH")" = "$sum_env" ]'
check "NOT reloaded (no bootout, no bootstrap)"    '! grep -qE "^(bootout|bootstrap)" "$FAKE_LOG"'
check "loaded state detected through 3000-line list" 'grep -q "already loaded" "$SB/out.txt"'

echo "5) bootstrap fails twice right after bootout (the EIO race), then succeeds"
new_sandbox; echo 2 > "$FAKE_FAIL"
run_helper 1; rc=$?
check "exit 0 after retry"                         '[ $rc -eq 0 ]'
check "3 bootstrap attempts"                        '[ "$(grep -c "^bootstrap" "$FAKE_LOG")" -eq 3 ]'

echo "6) launcher: PG args, watchdog, lock release"
new_sandbox; run_helper 1
printf 'export CRS_PG_HOST=real.host\nexport CRS_PG_PASSWORD=x\n' > "$ENV_SH"
cat > "$SB/bin/fake-crs" <<EOF
#!/bin/bash
echo "\$*" > "$SB/crs-args"
echo "\${CRS_BUILD_DIRECT:-unset}" > "$SB/crs-direct"
sleep 30
EOF
chmod +x "$SB/bin/fake-crs"
t0=$(date +%s)
HOME="$SB/home" TMPDIR="$SB/" CRS_BIN="$SB/bin/fake-crs" CRS_BUILD_WATCHDOG=2 \
  bash "$LAUNCHER" > "$SB/launcher.out" 2>&1; rc=$?
t1=$(date +%s)
check "watchdog fires: rc=142 within ~2s"          '[ $rc -eq 142 ] && [ $((t1 - t0)) -le 4 ]'
check "watchdog logged"                            'grep -q WATCHDOG "$SB/launcher.out"'
check "lock released afterwards"                   '[ ! -d "$SB/crs-build.lock.d" ]'
check "PG mode → --project-prefix=-Users-$U"       'grep -q -- "--project-prefix=-Users-$U" "$SB/crs-args"'
check "PG mode → CRS_BUILD_DIRECT=1"               '[ "$(cat "$SB/crs-direct")" = 1 ]'
check "--workers 2"                                'grep -q -- "--workers 2" "$SB/crs-args"'

echo "7) existing plist is corrupt (unparseable) — must refuse, not overwrite"
new_sandbox
printf '<?xml version="1.0"?><plist><dict><key>CRS_PG_PASSWORD</key><string>a&b</string></dict></plist>' > "$PLIST"
sum_bad="$(shasum "$PLIST")"
run_helper 1; rc=$?
check "exits non-zero"                             '[ $rc -ne 0 ]'
check "corrupt plist left exactly as it was"       '[ "$(shasum "$PLIST")" = "$sum_bad" ]'
check "no env.sh fabricated from error text"       '[ ! -f "$ENV_SH" ]'
check "tells the user why"                         'grep -q "Refusing to overwrite" "$SB/out.txt"'

echo "8) a correct plist from the template does not trip the placeholder grep"
new_sandbox; run_helper 1
check "no arcana.example.com anywhere in the plist" '! grep -q arcana.example.com "$PLIST"'
check "no REPLACE_WITH_ anywhere in the plist"      '! grep -q REPLACE_WITH_ "$PLIST"'

echo
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
