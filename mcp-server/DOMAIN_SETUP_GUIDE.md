# Step-by-Step: Setting Up verifimind.ysenseai.org

## STEP 1: Map Custom Domain in Google Cloud Console

### 1.1 Open Cloud Run Service
**Click this link to go directly to your service:**
https://console.cloud.google.com/run/detail/us-central1/verifimind-mcp-server/metrics?project=ysense-platform-v4-1

### 1.2 Navigate to Custom Domains
1. On the service page, click the **"MANAGE CUSTOM DOMAINS"** button (top right)
2. Or click this direct link: https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1

### 1.3 Add Domain Mapping
1. Click **"ADD MAPPING"** button
2. In the dropdown, select: **verifimind-mcp-server**
3. Enter domain: **verifimind.ysenseai.org**
4. Click **"CONTINUE"**

---

## STEP 2: Verify Domain Ownership (if not already verified)

### 2.1 Check if ysenseai.org is Already Verified
- Go to: https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1
- Look for "ysenseai.org" in the verified domains list

### 2.2 If NOT Verified, You'll Need to Verify
Google will show you a TXT record like:

```
Type: TXT
Name: @ (or ysenseai.org)
Value: google-site-verification=xxxxxxxxxxxxxxxxxxx
```

**Add this to your DNS provider**, then click "VERIFY" in Google Cloud Console.

---

## STEP 3: Get DNS Records from Google

After verification, Google will provide DNS records. You'll see something like:

### Option A: CNAME Record (Recommended)
```
Type:  CNAME
Name:  verifimind
Value: ghs.googlehosted.com.
TTL:   3600 (or 300)
```

### Option B: A Records (Alternative)
```
Type:  A
Name:  verifimind
Value: 216.239.32.21

Type:  A
Name:  verifimind
Value: 216.239.34.21

Type:  A
Name:  verifimind
Value: 216.239.36.21

Type:  A
Name:  verifimind
Value: 216.239.38.21
```

**Copy these records** - you'll need them for Step 4.

---

## STEP 4: Configure DNS at Your DNS Provider

### 4.1 Where is ysenseai.org Hosted?
Go to your DNS provider (examples: Cloudflare, GoDaddy, Namecheap, Route53, etc.)

### 4.2 Add DNS Record
**If using CNAME (recommended):**
1. Log into your DNS provider
2. Go to DNS management for **ysenseai.org**
3. Add new record:
   - **Type**: CNAME
   - **Name**: verifimind
   - **Target/Value**: ghs.googlehosted.com
   - **TTL**: 300 or Auto

**If using A records:**
1. Add 4 separate A records
2. All with **Name**: verifimind
3. Each pointing to the 4 IP addresses Google provided

### 4.3 Save Changes
- Click "Save" or "Add Record"
- DNS changes can take 15 minutes to 48 hours to propagate

---

## STEP 5: Wait for SSL Certificate Provisioning

After DNS is configured:
1. Google Cloud will automatically detect the DNS changes
2. It will provision an SSL certificate (usually 15-60 minutes)
3. You'll see the status in Cloud Console change to "Active"

---

## STEP 6: Test Your Custom Domain

### 6.1 Check DNS Propagation
```bash
nslookup verifimind.ysenseai.org
```

Should return Google's IP addresses.

### 6.2 Test Endpoints
```bash
# Root endpoint
curl https://verifimind.ysenseai.org/

# Health check
curl https://verifimind.ysenseai.org/health

# MCP config
curl https://verifimind.ysenseai.org/.well-known/mcp-config

# MCP endpoint (SSE)
curl https://verifimind.ysenseai.org/mcp
```

---

## STEP 7: Update Your MCP Client Configuration

Update your Claude Desktop config or other MCP clients to use:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}
```

---

## Troubleshooting

### DNS Not Propagating?
- Wait longer (can take up to 48 hours)
- Clear your DNS cache: `ipconfig /flushdns` (Windows)
- Check propagation: https://dnschecker.org/#CNAME/verifimind.ysenseai.org

### SSL Certificate Not Provisioning?
- Ensure DNS is correctly pointing to Google
- Check Cloud Run domain mapping status
- May take up to 24 hours in some cases

### Still Getting 404 Errors?
- Verify the domain mapping is "Active" in Cloud Console
- Ensure you're accessing HTTPS (not HTTP)
- Check Cloud Run logs: https://console.cloud.google.com/logs/query?project=ysense-platform-v4-1

---

## Quick Links Reference

- **Cloud Run Service**: https://console.cloud.google.com/run/detail/us-central1/verifimind-mcp-server/metrics?project=ysense-platform-v4-1
- **Domain Mappings**: https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1
- **Service Logs**: https://console.cloud.google.com/logs/query?project=ysense-platform-v4-1
- **DNS Checker**: https://dnschecker.org

---

## Current Deployment Info

- **Project**: ysense-platform-v4-1
- **Service**: verifimind-mcp-server
- **Region**: us-central1
- **Current URL**: https://verifimind-mcp-server-690976799907.us-central1.run.app
- **Target Domain**: verifimind.ysenseai.org
- **Status**: ✓ Deployed and Running

---

**Once DNS propagates, your VerifiMind MCP Server will be live at:**
# https://verifimind.ysenseai.org
