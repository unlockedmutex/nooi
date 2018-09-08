while true; do base64 /dev/urandom | head -c 20 > logsim; echo "" > logsim; sleep 0.2; done
