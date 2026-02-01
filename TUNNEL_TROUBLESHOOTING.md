# Cloudflare Tunnel Error 1033 - Root Cause & Fixes

## Exact problem (from your tunnel logs)

```
ERR Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity"
WRN ... your machine/network is getting its egress UDP to port 7844 (or others) blocked or dropped.
```

**Meaning:** cloudflared gets a URL (e.g. shanghai-mounted-manor-asks.trycloudflare.com) but **never connects** to Cloudflare. When you visit the URL, Cloudflare has no connector → Error 1033.

---

## Possible causes (in order of likelihood)

| # | Cause | Who controls it | Fix |
|---|-------|-----------------|-----|
| 1 | **UDP port 7844 blocked** | Firewall / antivirus / network | Use `--protocol http2` (TCP instead of UDP) |
| 2 | **Windows Firewall** blocking cloudflared | You | Allow cloudflared in Windows Firewall |
| 3 | **Antivirus** (Norton, McAfee, etc.) blocking | You | Add cloudflared to exceptions |
| 4 | **Corporate / school / public Wi‑Fi** | Admin | Use different network or HTTP/2 |
| 5 | **VPN** blocking or misrouting UDP | You | Try without VPN |
| 6 | **Router / ISP** blocking outbound UDP | ISP | Try HTTP/2; if still blocked, contact ISP |

---

## Fix #1: Use HTTP/2 instead of QUIC (try this first)

Run cloudflared with `--protocol http2` so it uses TCP instead of UDP:

```bat
cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2
```

`start-tunnel.bat` and `start-all.bat` have been updated to use this by default.

---

## Fix #2: Allow cloudflared in Windows Firewall (manual step)

1. Open **Windows Security** → **Firewall & network protection** → **Allow an app through firewall**
2. Click **Change settings**, then **Allow another app**
3. Browse to cloudflared (e.g. `C:\Program Files\cloudflared\cloudflared.exe` or wherever it is)
4. Ensure both **Private** and **Public** are checked
5. Click OK

---

## Fix #3: Use a different tunnel (ngrok, localtunnel, etc.)

If Cloudflare Tunnel still fails, you can use another tunnel:

- **ngrok:** https://ngrok.com (free tier available)
- **localtunnel:** `npx localtunnel --port 8000`

These use different protocols and may work where Cloudflare does not.
