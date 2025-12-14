#!/bin/sh
case "$(echo "$DEBUG" | tr '[:upper:]' '[:lower:]')" in
	1|true|yes|on)
		echo "==== ENVIRONMENT VARIABLES ===="
		echo "ZONE_NAME:        $ZONE_NAME"
		echo "API_TOKEN:        $API_TOKEN"
		echo "RECORD_TYPE:      $RECORD_TYPE"
		echo "RECORD_NAME:      $RECORD_NAME"
		echo "INTERVAL:         $INTERVAL"
		echo "HETZNER_API_TYPE: $HETZNER_API_TYPE"
		echo "==============================="
		;;
esac
exec python -u hetzner_ddns.py
	exec python -u hetzner_ddns.py
