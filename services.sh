#!/bin/bash

# Application services only (postgres and redis stay running)
SERVICES="platform_api bot_runner streamlit_portal"

COMMAND=${1:-restart}  # Default to restart if no command provided

case "$COMMAND" in
    start)
        echo "Starting services: $SERVICES..."
        # Using 'up -d' ensures containers are created if missing and config changes are applied
        sudo docker compose up -d $SERVICES
        ;;
    stop)
        echo "Stopping services: $SERVICES..."
        sudo docker compose stop $SERVICES
        ;;
    restart)
        echo "Restarting services: $SERVICES..."
        echo "Stopping application containers..."
        sudo docker compose stop $SERVICES
        sudo docker compose rm -f $SERVICES
        echo "Starting services..."
        sudo docker compose up -d $SERVICES
        ;;
    *)
        echo "Invalid command: $COMMAND"
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
