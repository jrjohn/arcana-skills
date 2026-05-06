#!/bin/bash
# Dispatch only LibreNMS-approved checks based on $SSH_ORIGINAL_COMMAND
case "$SSH_ORIGINAL_COMMAND" in
  check_p33_threatfeed.sh)   exec ${MIS_HOME:-/opt/mis-log-db}/check_p33_threatfeed.sh ;;
  check_deny_inbound.sh)     exec ${MIS_HOME:-/opt/mis-log-db}/check_deny_inbound.sh ;;
  check_deny_outbound.sh)    exec ${MIS_HOME:-/opt/mis-log-db}/check_deny_outbound.sh ;;
  check-fg-threatfeed-inbound.sh) exec ${MIS_HOME:-/opt/mis-log-db}/check-fg-threatfeed-inbound.sh ;;
  *)  echo "UNKNOWN - command not allowed: $SSH_ORIGINAL_COMMAND"; exit 3 ;;
esac
