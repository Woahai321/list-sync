# 🌐 ListSync Domain Deployment Guide
## Separate Subdomains for Frontend & Backend

This guide shows how to deploy ListSync using separate subdomains for frontend and backend without reverse proxy.

## 🏗️ **Architecture Overview**

```
your-domain.com (Frontend - Port 3222)
    ↓ API calls to ↓
back.your-domain.com (Backend API - Port 4222)
```

**Benefits:**
- ✅ No reverse proxy complexity  
- ✅ Clear separation of frontend/backend
- ✅ Easy SSL certificate management per subdomain
- ✅ Simple DNS configuration
- ✅ CORS handled properly between subdomains

## 📋 **Prerequisites**

1. **Domain name** (e.g., `your-domain.com`)
2. **DNS access** to create subdomain
3. **SSL certificates** for both domains
4. **Server** with Docker and Docker Compose

## 🔧 **Step-by-Step Setup**

### 1. **DNS Configuration**

Set up DNS A records pointing to your server IP:

```
your-domain.com        A    YOUR_SERVER_IP
back.your-domain.com   A    YOUR_SERVER_IP
```

### 2. **Update .env Configuration**

Your `.env` file should look like this:

```bash
# === Domain Configuration ===
FRONTEND_DOMAIN=your-domain.com
BACKEND_DOMAIN=back.your-domain.com

# === API Configuration ===
NEXT_PUBLIC_API_URL=https://back.your-domain.com/api

# === CORS Configuration ===
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# === Your existing config ===
OVERSEERR_URL=https://your-overseerr-instance.com
OVERSEERR_API_KEY=your-api-key-here
# ... rest of your configuration
```

### 3. **SSL Certificates**

You'll need SSL certificates for both domains. Using Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot

# Get certificates for both domains
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
sudo certbot certonly --standalone -d back.your-domain.com

# Note: You'll need to configure your web server (Apache/nginx on host) 
# to handle SSL termination and proxy to Docker ports
```

### 4. **Host Web Server Configuration**

Since you're not using nginx in Docker, configure your host web server:

#### **Apache Configuration (`/etc/apache2/sites-available/`):**

**your-domain.com.conf:**
```apache
<VirtualHost *:443>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/your-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your-domain.com/privkey.pem
    
    ProxyPreserveHost On
    ProxyPass / http://localhost:3222/
    ProxyPassReverse / http://localhost:3222/
</VirtualHost>

<VirtualHost *:80>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>
```

**back.your-domain.com.conf:**
```apache
<VirtualHost *:443>
    ServerName back.your-domain.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/back.your-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/back.your-domain.com/privkey.pem
    
    ProxyPreserveHost On
    ProxyPass / http://localhost:4222/
    ProxyPassReverse / http://localhost:4222/
    
    # CORS headers
    Header always set Access-Control-Allow-Origin "https://your-domain.com"
    Header always set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
    Header always set Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization"
    Header always set Access-Control-Allow-Credentials "true"
</VirtualHost>

<VirtualHost *:80>
    ServerName back.your-domain.com
    Redirect permanent / https://back.your-domain.com/
</VirtualHost>
```

#### **nginx Configuration (alternative):**

**your-domain.com:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com www.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3222;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**back.your-domain.com:**
```nginx
server {
    listen 443 ssl;
    server_name back.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/back.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/back.your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:4222;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://your-domain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
        add_header Access-Control-Allow-Credentials "true" always;
    }
}

server {
    listen 80;
    server_name back.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. **Deploy Application**

```bash
# Build and start with domain configuration
docker-compose -f docker-compose.domain.yml up -d

# Check status
docker-compose -f docker-compose.domain.yml ps

# View logs
docker-compose -f docker-compose.domain.yml logs -f
```

### 6. **Verify Deployment**

Test both domains:

```bash
# Test frontend
curl -k https://your-domain.com

# Test backend API
curl -k https://back.your-domain.com/api/system/health

# Test CORS (from browser console on your-domain.com)
fetch('https://back.your-domain.com/api/system/health')
```

## 🌐 **How It Works**

### **Request Flow:**
1. User visits `https://your-domain.com`
2. Host web server (Apache/nginx) proxies to Docker port 3222
3. Frontend makes API calls to `https://back.your-domain.com/api/*`
4. Host web server proxies API requests to Docker port 4222
5. CORS allows cross-subdomain communication

### **CORS Configuration:**
- Frontend domain: `https://your-domain.com`
- Backend domain: `https://back.your-domain.com`  
- CORS allows `your-domain.com` to access `back.your-domain.com`

## 📊 **Access Points**

- **🎨 Frontend Dashboard**: https://your-domain.com
- **🔗 API Documentation**: https://back.your-domain.com/docs
- **❤️ API Health Check**: https://back.your-domain.com/api/system/health

## 🛠 **Troubleshooting**

### **Common Issues:**

1. **CORS errors:**
   ```bash
   # Check CORS headers
   curl -H "Origin: https://your-domain.com" -I https://back.your-domain.com/api/system/health
   ```

2. **SSL certificate issues:**
   ```bash
   # Check certificate validity
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   openssl s_client -connect back.your-domain.com:443 -servername back.your-domain.com
   ```

3. **DNS resolution:**
   ```bash
   # Check DNS records
   nslookup your-domain.com
   nslookup back.your-domain.com
   ```

4. **Container connectivity:**
   ```bash
   # Test internal ports
   curl http://localhost:3222
   curl http://localhost:4222/api/system/health
   ```

## 🔄 **SSL Certificate Renewal**

Set up automatic renewal for both domains:

```bash
# Create renewal script
cat > renew-ssl.sh << 'EOF'
#!/bin/bash
sudo certbot renew --quiet
sudo systemctl reload apache2  # or nginx
EOF

chmod +x renew-ssl.sh

# Add to crontab (run monthly)
echo "0 0 1 * * /path/to/renew-ssl.sh" | crontab -
```

## ✅ **Final Checklist**

- [ ] DNS A records point to your server
- [ ] SSL certificates obtained for both domains
- [ ] Host web server configured for both domains
- [ ] `.env` updated with correct domains
- [ ] Docker application deployed
- [ ] Frontend accessible at `https://your-domain.com`
- [ ] API accessible at `https://back.your-domain.com/api/system/health`
- [ ] No CORS errors in browser console
- [ ] SSL certificates set to auto-renew

---

## 🎯 **Advantages of This Approach**

- **Simple deployment** - No complex reverse proxy in Docker
- **Clear separation** - Frontend and backend have distinct domains
- **Easy scaling** - Can move frontend/backend to different servers later
- **SSL flexibility** - Independent SSL management per subdomain
- **Standard setup** - Uses conventional web server configuration 