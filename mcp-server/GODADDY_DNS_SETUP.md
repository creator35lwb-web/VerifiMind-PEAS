# Quick Setup: Add verifimind.ysenseai.org (GoDaddy)

## Good News! 🎉
Your domain **ysenseai.org** is already configured with Google Cloud and hosted on **GoDaddy**. You just need to add one subdomain record.

---

## STEP 1: Access Google Cloud Console

**Click here to set up domain mapping:**
https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1

1. Click **"ADD MAPPING"**
2. Select service: **verifimind-mcp-server**
3. Enter domain: **verifimind.ysenseai.org**
4. Click **"CONTINUE"**

Since ysenseai.org is already verified, you'll skip verification and go straight to DNS configuration.

Google will show you the DNS records needed (likely CNAME).

---

## STEP 2: Add DNS Record in GoDaddy

### 2.1 Log into GoDaddy
1. Go to https://dcc.godaddy.com/
2. Log in with your credentials
3. Click on **"My Products"**
4. Find **ysenseai.org** and click **"DNS"** or **"Manage DNS"**

**Direct link to DNS management:**
https://dcc.godaddy.com/control/portfolio/ysenseai.org/settings?subtab=dns

### 2.2 Add CNAME Record

Click **"Add"** button, then:

| Field | Value |
|-------|-------|
| **Type** | CNAME |
| **Name** | verifimind |
| **Value** | ghs.googlehosted.com |
| **TTL** | 600 seconds (or 1 hour) |

**Screenshot reference:**
```
┌─────────────────────────────────────────┐
│ Add DNS Record                          │
├─────────────────────────────────────────┤
│ Type:     [CNAME ▼]                     │
│ Name:     [verifimind]                  │
│ Value:    [ghs.googlehosted.com]        │
│ TTL:      [1 Hour ▼]                    │
│                                         │
│ [Cancel]              [Save]            │
└─────────────────────────────────────────┘
```

### 2.3 Alternative: Using A Records

If GoDaddy doesn't allow CNAME for some reason, add these **4 A records** instead:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | verifimind | 216.239.32.21 | 600 |
| A | verifimind | 216.239.34.21 | 600 |
| A | verifimind | 216.239.36.21 | 600 |
| A | verifimind | 216.239.38.21 | 600 |

### 2.4 Save Changes
- Click **"Save"** or **"Add Record"**
- GoDaddy usually propagates in 10-30 minutes (can take up to 48 hours)

---

## STEP 3: Wait for Google to Provision SSL Certificate

1. Go back to Google Cloud Console: https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1
2. Watch the domain mapping status change from "Pending" to "Active"
3. This usually takes 15-60 minutes after DNS propagates

---

## STEP 4: Test Your Setup

### Check DNS Propagation (Windows Command Prompt)
```bash
nslookup verifimind.ysenseai.org
```

Should show Google's IPs:
```
Name:    verifimind.ysenseai.org
Addresses:  216.239.32.21
            216.239.34.21
            216.239.36.21
            216.239.38.21
```

### Test HTTPS Endpoints
```bash
curl https://verifimind.ysenseai.org/health
curl https://verifimind.ysenseai.org/
```

Should return JSON responses.

---

## Visual Guide

### Your Current Setup:
```
ysenseai.org  ──→  Google Cloud (already configured ✓)
```

### What You're Adding:
```
verifimind.ysenseai.org  ──→  verifimind-mcp-server (Cloud Run)
                               us-central1
```

### Complete Architecture After Setup:
```
┌─────────────────────────────────────────────────┐
│  ysenseai.org (GoDaddy DNS)                     │
│                                                 │
│  ├─ ysenseai.org                                │
│  │  └─→ Google Cloud (existing)                │
│                                                 │
│  └─ verifimind.ysenseai.org (NEW!)              │
│     └─→ ghs.googlehosted.com                    │
│        └─→ Cloud Run: verifimind-mcp-server     │
│           └─→ MCP Server (HTTP-SSE)             │
└─────────────────────────────────────────────────┘
```

---

## Quick Reference Card

| What | Where | Link |
|------|-------|------|
| **GoDaddy DNS** | Manage DNS Records | https://dcc.godaddy.com/control/portfolio/ysenseai.org/settings?subtab=dns |
| **Google Cloud** | Add Domain Mapping | https://console.cloud.google.com/run/domains?project=ysense-platform-v4-1 |
| **Test DNS** | DNS Checker | https://dnschecker.org/#CNAME/verifimind.ysenseai.org |
| **View Logs** | Cloud Run Logs | https://console.cloud.google.com/logs/query?project=ysense-platform-v4-1 |

---

## Expected Timeline

| Step | Duration |
|------|----------|
| Add DNS record in GoDaddy | 2 minutes |
| DNS propagation | 10-30 minutes (max 48 hours) |
| Google SSL certificate | 15-60 minutes |
| **Total** | ~30-90 minutes |

---

## Troubleshooting

### CNAME vs A Records?
- **CNAME is recommended** (easier to maintain)
- Use A records only if CNAME doesn't work

### DNS Not Updating?
```bash
# Flush DNS cache (Windows)
ipconfig /flushdns

# Check again
nslookup verifimind.ysenseai.org
```

### Still See Old DNS?
- Wait longer (DNS propagation varies by location)
- Check multiple DNS checkers:
  - https://dnschecker.org
  - https://www.whatsmydns.net

---

**Ready to go!** 🚀

Once complete, share this URL with your MCP clients:
```
https://verifimind.ysenseai.org/mcp
```
