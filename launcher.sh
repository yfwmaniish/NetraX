#!/bin/bash



# Check if Privoxy is running
if pgrep -x "privoxy" > /dev/null
then
    echo "✅ Privoxy is running."
else
    echo "❌ Privoxy is NOT running! Attempting to start it..."
    privoxy /etc/privoxy/config &
    sleep 3
    if pgrep -x "privoxy" > /dev/null
    then
        echo "✅ Privoxy started successfully."
    else
        echo "❌ Failed to start Privoxy. Please check manually!"
        exit 1
    fi
fi

clear
echo -e "\033[1;36m"
cat <<'EOF'
$$\   $$\ $$\   $$\    $$\    $$\   $$\  $$$$$$\  $$$$$$$\  $$\   $$\  $$$$$$\  $$\   $$\ 
$$ |  $$ |$$ |  $$ | $$$$$$\  $$ |  $$ |$$  __$$\ $$  __$$\ $$ |  $$ |$$  __$$\ $$ | $$  |
$$ |  $$ |$$ |  $$ |$$  __$$\ $$ |  $$ |$$ /  \__|$$ |  $$ |$$ |  $$ |$$ /  \__|$$ |$$  / 
$$$$$$$$ |$$$$$$$$ |$$ /  \__|$$$$$$$$ |$$ |      $$$$$$$  |$$$$$$$$ |$$ |      $$$$$  /  
$$  __$$ |\_____$$ |\$$$$$$\  $$  __$$ |$$ |      $$  __$$< \_____$$ |$$ |      $$  $$<   
$$ |  $$ |      $$ | \___ $$\ $$ |  $$ |$$ |  $$\ $$ |  $$ |      $$ |$$ |  $$\ $$ |\$$\  
$$ |  $$ |      $$ |$$\  \$$ |$$ |  $$ |\$$$$$$  |$$ |  $$ |      $$ |\$$$$$$  |$$ | \$$\ 
\__|  \__|      \__|\$$$$$$  |\__|  \__| \______/ \__|  \__|      \__| \______/ \__|  \__|
                     \_$$  _/                                                             
                       \ _/                                                               
EOF
echo -e "\033[0m"

echo " "

# ✍️ Ask user for onion URL
read -p "🔗 Enter the starting .onion URL (with http:// or https://) : " START_URL

# If no input, exit
if [ -z "$START_URL" ]; then
  echo "❌ No URL entered! Exiting."
  exit 1
fi

echo ""
echo "🚀 Starting Decimal Darkweb Monitoring..."
echo ""

# Start crawler
echo "🔎 Starting crawler..."
python3 crawler/decimal_crawler.py "$START_URL" &
CRAWLER_PID=$!

# Start Flask dashboard
echo "🖥  Starting Flask dashboard..."
python3 dashboard/decimal_dashboard.py &
FLASK_PID=$!

echo ""
echo "═════════════════════════════════════════════"
echo "🌐 Both Crawler (PID $CRAWLER_PID) and Flask (PID $FLASK_PID) started."
echo "🌐 Visit dashboard at: http://127.0.0.1:5000"
echo "═════════════════════════════════════════════"

# Trap CTRL+C and kill both processes
trap ctrl_c INT

function ctrl_c() {
    echo ""
    echo "🛑 Stopping monitoring..."
    kill $CRAWLER_PID
    kill $FLASK_PID
    echo "👋 Monitoring stopped. Bye!"
    exit
}

# Wait forever
wait
