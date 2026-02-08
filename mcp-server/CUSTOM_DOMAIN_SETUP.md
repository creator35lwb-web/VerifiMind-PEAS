# Custom Domain Setup for VerifiMind MCP Server

## Deployment Status: SUCCESS ✓

Your MCP server is now live at:
- **Service URL**: https://verifimind.ysenseai.org
- **Health**: https://verifimind.ysenseai.org/health
- **MCP Config**: https://verifimind.ysenseai.org/.well-known/mcp-config
- **MCP Endpoint**: https://verifimind.ysenseai.org/mcp

## Setting Up Custom Domain: verifimind.ysenseai.org

### Option 1: Using Google Cloud Console (Recommended)

1. **Navigate to Cloud Run**
   - Go to https://console.cloud.google.com/run
   - Select your project: `YOUR_GCP_PROJECT_ID`
   - Click on service: `verifimind-mcp-server`

2. **Add Custom Domain**
   - Click on the "INTEGRATIONS" tab
   - Click "MANAGE CUSTOM DOMAINS"
   - Click "ADD MAPPING"
   - Select service: `verifimind-mcp-server`
   - Enter domain: `verifimind.ysenseai.org`
   - Click "CONTINUE"

3. **Verify Domain Ownership**
   - If you haven't verified `ysenseai.org` yet, you'll need to:
     - Add a TXT record to your DNS provider
     - Wait for verification (usually a few minutes)

4. **Get DNS Records**
   - After verification, Google will provide DNS records
   - You'll typically need to add:
     - **CNAME record**: `mcp` → `ghs.googlehosted.com`
     - Or **A records** pointing to Google's IP addresses

5. **Update DNS**
   - Go to your DNS provider (where ysenseai.org is hosted)
   - Add the DNS records provided by Google Cloud
   - Wait for propagation (15 minutes to 48 hours)

### Option 2: Using gcloud CLI

```bash
# Install beta components (run as Administrator)
gcloud components install beta

# Create domain mapping
gcloud beta run domain-mappings create \
  --service verifimind-mcp-server \
  --domain verifimind.ysenseai.org \
  --region us-central1

# Get DNS records to configure
gcloud beta run domain-mappings describe verifimind.ysenseai.org \
  --region us-central1
```

### Option 3: Using Cloud Load Balancer (Most Flexible)

If you want SSL, CDN, and more control:

1. Create a global external IP
2. Create a serverless NEG (Network Endpoint Group) for Cloud Run
3. Create a backend service
4. Create a URL map
5. Create a target HTTPS proxy with SSL certificate
6. Create a forwarding rule
7. Point your DNS A record to the reserved IP

This is more complex but gives you full control over SSL certificates, CDN, etc.

## DNS Configuration Example

Once domain mapping is complete, add these records to your DNS:

```
Type:  CNAME
Name:  verifimind
Value: ghs.googlehosted.com
TTL:   300
```

Or if Google provides A records:

```
Type:  A
Name:  verifimind
Value: 216.239.32.21
TTL:   300

Type:  A
Name:  verifimind
Value: 216.239.34.21
TTL:   300

Type:  A
Name:  verifimind
Value: 216.239.36.21
TTL:   300

Type:  A
Name:  verifimind
Value: 216.239.38.21
TTL:   300
```

## Testing After DNS Propagation

```bash
# Check DNS propagation
nslookup verifimind.ysenseai.org

# Test endpoints
curl https://verifimind.ysenseai.org/health
curl https://verifimind.ysenseai.org/.well-known/mcp-config
curl https://verifimind.ysenseai.org/
```

## Important Notes

1. **SSL Certificate**: Google Cloud Run automatically provisions SSL certificates for custom domains
2. **Propagation Time**: DNS changes can take 15 minutes to 48 hours
3. **Domain Verification**: Required before mapping (one-time per domain)
4. **Subdomain**: You're adding `verifimind.ysenseai.org`, so verify the root `ysenseai.org` first

## Current Configuration

- **Project**: YOUR_GCP_PROJECT_ID
- **Service**: verifimind-mcp-server
- **Region**: us-central1
- **Memory**: 512Mi
- **CPU**: 1
- **Max Instances**: 10
- **Environment**:
  - LLM_PROVIDER=mock
  - ENABLE_LOGGING=true

## Next Steps

1. Choose one of the options above to set up the custom domain
2. Configure DNS records as instructed
3. Wait for DNS propagation
4. Test the endpoints at `https://verifimind.ysenseai.org`
5. Update your MCP client configuration to use `https://verifimind.ysenseai.org`
