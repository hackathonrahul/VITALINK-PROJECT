# 📱 Mobile Access Guide - Vitalink

The Vitalink server is configured to be accessible from mobile devices on the same network. Follow the steps below to access it from your smartphone or tablet.

## ✅ Server Status

**Server is running on:**
- **Local (Desktop):** `http://localhost:5000`
- **Network IP:** `http://10.0.2.90:5000` or `http://172.17.0.1:5000`
- **All available on port:** `5000`

## 📱 Access from Mobile Device

### Prerequisites
- Mobile device (iOS/Android) connected to the same network as the server
- Web browser installed on the device

### Step-by-Step Instructions

#### 1. **Find Your Server IP Address**
Run this command to get the server's network IP:
```bash
hostname -I
```

Look for an IP address like `10.0.x.x` or `192.168.x.x` (not `127.0.0.1`)

#### 2. **Open Mobile Browser**
- Open any web browser on your mobile device (Chrome, Safari, Firefox, etc.)

#### 3. **Enter the URL**
Replace `<SERVER_IP>` with the IP from step 1:
```
http://<SERVER_IP>:5000
```

**Example:**
- `http://10.0.2.90:5000`
- `http://192.168.1.100:5000`

#### 4. **Access the App**
You should see the Vitalink login page. Register or login and use the app normally!

---

## 🔍 Troubleshooting

### ❌ "Cannot connect to server"
**Solution:**
1. Ensure both devices are on the **same Wi-Fi network**
2. Verify server is running: `ps aux | grep vitalink`
3. Check firewall is not blocking port 5000
4. Use the correct IP address (not `localhost` or `127.0.0.1` from mobile)

### ❌ "Connection timed out"
**Solution:**
1. Run `netstat -tlnp 2>/dev/null | grep 5000` to verify port is listening
2. Restart server:
   ```bash
   pkill -f "python.*vitalink" && sleep 2
   cd /workspaces/VITALINK-PROJECT && python vitalink.py &
   sleep 3
   ```

### ❌ "Page not loading on mobile"
**Solution:**
1. Check mobile device has internet/Wi-Fi enabled
2. Try accessing from a different device on the same network
3. Verify server is still running (see above)

---

## 🚀 Quick Start Commands

### Start the Server
```bash
cd /workspaces/VITALINK-PROJECT
python vitalink.py &
```

### Get Network IP
```bash
hostname -I | awk '{print $1}'
```

### Stop the Server
```bash
pkill -f "python.*vitalink"
```

### Check Server Status
```bash
ps aux | grep vitalink | grep -v grep
```

---

## 📲 What Works on Mobile

✅ **User Registration & Login**  
✅ **View Profile & Edit Details**  
✅ **Book Doctor Appointments**  
✅ **Book Wellness Classes**  
✅ **View My Appointments**  
✅ **Chat with AI Health Assistant**  
✅ **Upload & Process Health Reports (OCR)**  
✅ **Access Wellness Hub**  

---

## 🔒 Security Notes

- This is a **development server** for local testing only
- Do NOT expose to the internet without proper security (HTTPS, firewall, authentication)
- Server runs in debug mode - suitable for development but not production
- For production deployment, use a proper WSGI server (Gunicorn, uWSGI, etc.)

---

## 📞 Need Help?

If you encounter issues:
1. Check server logs: `tail -f /tmp/flask.log`
2. Verify network connectivity between devices
3. Ensure you're using the correct IP address and port
4. Restart the server and try again

---

**Happy testing! 🎉**
