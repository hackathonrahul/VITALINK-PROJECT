#!/bin/bash

# 📱 Vitalink Mobile Access Setup Script
# This script helps you set up and verify mobile access to Vitalink

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 VITALINK MOBILE ACCESS SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "1️⃣  CHECKING SERVER STATUS..."
echo ""

if ps aux | grep -q "[p]ython.*vitalink"; then
    echo "✅ Server is RUNNING"
else
    echo "❌ Server is NOT running"
    echo "   Starting server..."
    cd /workspaces/VITALINK-PROJECT
    python vitalink.py > /tmp/flask.log 2>&1 &
    sleep 3
    echo "✅ Server started"
fi

echo ""
echo "2️⃣  GETTING NETWORK INFORMATION..."
echo ""

# Get network IPs
echo "📡 Available network addresses:"
hostname -I | tr ' ' '\n' | while read ip; do
    if [[ $ip != "127.0.0.1" ]] && [[ ! -z "$ip" ]]; then
        echo "   🔗 http://$ip:5000"
    fi
done

echo ""
echo "3️⃣  PORT VERIFICATION..."
echo ""

if netstat -tlnp 2>/dev/null | grep -q ":5000"; then
    echo "✅ Port 5000 is LISTENING"
    netstat -tlnp 2>/dev/null | grep ":5000" | awk '{print "   " $0}'
else
    echo "❌ Port 5000 is NOT listening"
    exit 1
fi

echo ""
echo "4️⃣  SERVER CONNECTIVITY TEST..."
echo ""

if curl -s http://localhost:5000/ | grep -q "Welcome"; then
    echo "✅ Server is RESPONDING correctly"
else
    echo "❌ Server is NOT responding"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 MOBILE ACCESS INSTRUCTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "On your mobile device:"
echo ""
echo "1. Connect to the SAME Wi-Fi network as your computer"
echo "2. Open a web browser (Chrome, Safari, Firefox)"
echo "3. Enter this address in the URL bar:"
echo ""

# Get primary network IP (not loopback)
PRIMARY_IP=$(hostname -I | awk '{for(i=1;i<=NF;i++) if($i != "127.0.0.1") {print $i; exit}}')
echo "   📱 http://$PRIMARY_IP:5000"
echo ""
echo "4. You should see the Vitalink login page"
echo "5. Register or login and start using the app!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Setup Complete! Your app is mobile-ready."
echo ""
