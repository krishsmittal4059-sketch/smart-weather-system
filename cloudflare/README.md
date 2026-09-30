# Cloudflare Tunnel setup

This makes the Smart Weather web dashboard reachable through a public HTTPS hostname without entering the Pi IP in the phone browser.

A persistent Cloudflare hostname requires a Cloudflare account and a domain. Follow Cloudflare's official Tunnel dashboard setup.

## Pi setup

1. Install `cloudflared` using the ARM/Linux package or command shown by the Cloudflare dashboard.
2. Verify with `cloudflared --version`.
3. In Cloudflare: Networking -> Tunnels -> Create Tunnel. Name it `smart-weather`.
4. Select the Raspberry Pi/Linux architecture and copy the connector command shown by Cloudflare.
5. Add a Published application route with your chosen hostname, such as `weather.your-domain.com`.
6. Set the Service URL to `http://localhost:5000`.
7. On the Pi run the weather server:

    cd ~/smart_weather_system
    python3 app.py

8. Install/run the Cloudflare connector using the command supplied by your Cloudflare dashboard.
9. Check it with `sudo systemctl status cloudflared`.

Then open your chosen HTTPS hostname on the phone. No Pi IP is required.

Never put Cloudflare tokens, credentials, or private certificates in GitHub.

## Temporary testing

For development only, Cloudflare also provides Quick Tunnels:

    cloudflared tunnel --url http://localhost:5000

This produces a temporary `trycloudflare.com` address. Use a named tunnel for a persistent project URL.
