#!/bin/bash
# Check if a port is available and suggest alternatives if not

PORT=${1:-8000}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while [ $port -lt 9000 ]; do
        if ! is_port_in_use $port; then
            echo $port
            return
        fi
        ((port++))
    done
    echo "No available ports found"
}

# Check if requested port is in use
if is_port_in_use $PORT; then
    echo "⚠️  WARNING: Port $PORT is already in use!"
    echo ""

    # Find process using the port
    PROCESS=$(lsof -i :$PORT -sTCP:LISTEN | tail -n 1)
    if [ ! -z "$PROCESS" ]; then
        echo "Process using port $PORT:"
        echo "$PROCESS"
        echo ""
    fi

    # Suggest alternative port
    ALTERNATIVE=$(find_available_port $((PORT + 1)))
    echo "Suggested alternative: Port $ALTERNATIVE"
    echo ""
    echo "To use a different port, update your .env file:"
    echo "  PORT=$ALTERNATIVE"
    echo ""
    echo "Or run with environment variable:"
    echo "  PORT=$ALTERNATIVE docker compose up"
    echo ""
    exit 1
else
    echo "✅ Port $PORT is available"
    exit 0
fi
