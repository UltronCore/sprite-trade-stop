# Hosting Guide — Sprite Trade Stop Discord Bot

This guide explains how to keep the **Sprite Trade Stop** bot running 24/7. It is written for a **non-coder** — if you have never opened a terminal in your life, you can still follow this. Read the section that fits your budget and comfort level, then do exactly what it says, line by line.

> **The bot is just one program** (`python bot.py`) that uses one small local database file (SQLite). It does not need much. Any of the options below will run it.

---

## ⚠️ Read this first — Discord setup (required no matter where you host)

Before the bot will work properly, two things must be set in the Discord Developer Portal and your server. **Hosting will not fix these — they are separate.**

1. **Turn on "Message Content Intent"**
   - Go to <https://discord.com/developers/applications>
   - Click your bot's application → **Bot** (left menu).
   - Scroll to **Privileged Gateway Intents** and switch **MESSAGE CONTENT INTENT** to **ON**, then **Save**.
   - This is required for the `/insights` feature to read messages and for the `+rep` text alias.

2. **Put the bot's role ABOVE the sprite/flair/verified roles**
   - In your Discord server: **Server Settings → Roles**.
   - **Drag the bot's role up** so it sits **above every sprite role, flair role, and the verified role** it needs to manage.
   - Make sure the bot's role has the **Manage Roles** permission.
   - Discord rule: a bot can only add or remove roles that are **lower** than its own role. If its role is too low, it will silently fail to assign roles.

**Keep your bot token secret.** It goes in a file called `.env` (or a token box in a hosting panel). Never paste it into a public chat. If it ever leaks, reset it in the Developer Portal → Bot → **Reset Token**.

---

## Quick comparison

| Option | Cost | Difficulty | Always-on? | Notes |
|---|---|---|---|---|
| **Oracle Cloud Always Free** (Arm VM) | **Free forever** | Hard (real Linux server) | ✅ Yes, true 24/7 | Best free option. Needs a credit card to verify (not charged). Most setup work. |
| **Bot-Hosting.net** (free) | **Free** (earn "coins" daily) | Easy (web panel, no Linux) | ⚠️ Mostly — relies on claiming free coins to keep it funded | 256 MB RAM, drag-and-drop upload. Fine for a small bot. |
| **Pella** (pella.app, free) | **Free** | Easy (web panel, no Linux) | ❌ Not truly 24/7 — free containers need **manual renewal every ~24h** | Good for testing, not for set-and-forget. |
| **Hetzner CX22** | **~€4.35 / ~$4.59 a month** | Medium (Linux server) | ✅ Yes, true 24/7 | Best value paid VPS. 2 vCPU, 4 GB RAM, 40 GB disk. |
| **DigitalOcean** basic droplet | **From $4 a month** | Medium (Linux server) | ✅ Yes, true 24/7 | Friendliest paid dashboard. Cheapest is 1 vCPU, 512 MB RAM, 10 GB disk. |

> 💡 **Recommendation:** If you want free and reliable, use **Oracle Cloud**. If you want easy and free, use **Bot-Hosting.net**. If you want easy, reliable, and don't mind ~$5/month, use **Hetzner** or **DigitalOcean**.

---

# (A) FREE PATH

## A1. PRIMARY — Oracle Cloud Always Free (recommended free option)

Oracle gives away a genuinely free, always-on virtual server (a "VM"). As of the prices verified for this guide (June 2026), the **Always Free** tier includes:

- Up to **4 Arm CPUs (OCPUs)** and **24 GB of RAM** on Ampere A1 machines (you can use it all in one VM).
- **200 GB** of storage.
- **10 TB** of outbound internet traffic per month.
- **Free forever** (not a trial), as long as you stay within those limits and keep everything in your "home region."

This is far more than the bot needs. The catch: it's a real Linux server, so there are more steps. Go slowly and copy commands exactly.

> You'll need a **credit/debit card to verify your identity**. Oracle does **not** charge it for Always Free resources.

### Step 1 — Sign up
1. Go to <https://www.oracle.com/cloud/free/> and click **Start for free**.
2. Enter your email, choose your **country/region** (this becomes your "home region" — pick the one closest to you, you can't change it later).
3. Verify your email, set a password, enter your address and the card for verification.
4. Wait for the account to finish setting up (can take a few minutes to an hour). You'll get an email when it's ready.

### Step 2 — Create the server (Ubuntu VM)
1. Sign in at <https://cloud.oracle.com>.
2. In the top search bar, type **Instances** and click **Instances** (under Compute).
3. Click **Create instance**.
4. **Name:** type `sprite-trade-stop`.
5. **Image and shape:**
   - Click **Edit** next to "Image and shape."
   - **Change image** → choose **Canonical Ubuntu** (pick **24.04** or **22.04**) → **Select image**.
   - **Change shape** → choose **Ampere** → **VM.Standard.A1.Flex**. Set it to **1 OCPU and 6 GB memory** (plenty for the bot). Click **Select shape**.
6. **Add SSH keys** — this is how you log in.
   - Choose **Generate a key pair for me**.
   - Click **Save private key** and **Save public key**. Keep the **private key** file somewhere safe on your computer (e.g. a folder called `sprite-keys`). You will need it to log in.
7. Leave networking on the default ("Create new virtual cloud network"). Make sure **Assign a public IPv4 address** is checked.
8. Click **Create**. Wait until the instance status turns **green / Running**.
9. **Write down the "Public IP address"** shown on the instance page. You'll use it to connect.

### Step 3 — Connect to the server (SSH)
"SSH" just means "log in to the server remotely."

**On Mac:**
1. Open the **Terminal** app (press `Cmd+Space`, type `Terminal`, Enter).
2. Lock down your key (replace the path with where you saved your private key):
   ```
   chmod 600 ~/Downloads/ssh-key-*.key
   ```
3. Connect (replace `YOUR.IP.ADDRESS` with the public IP, and the key path with yours):
   ```
   ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR.IP.ADDRESS
   ```
4. The first time, it asks "Are you sure you want to continue connecting?" — type `yes` and press Enter.

**On Windows:**
1. Open the **PowerShell** app (Start menu → type `PowerShell`).
2. Connect (replace with your key path and IP):
   ```
   ssh -i C:\Users\YOU\Downloads\ssh-key-2026.key ubuntu@YOUR.IP.ADDRESS
   ```
3. Type `yes` if prompted.

You're now "inside" the server. The prompt changes to something like `ubuntu@sprite-trade-stop:~$`.

### Step 4 — Install the tools the bot needs
Copy and paste these one line at a time, pressing Enter after each:

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git
```

(If asked anything, just press Enter to accept defaults.)

### Step 5 — Download (clone) and set up the bot
Replace `<repo-url>` with the actual address of your bot's code repository.

```
git clone <repo-url> && cd sprite-trade-stop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Step 6 — Add your bot token
Open the secret config file in a simple editor:
```
nano .env
```
- Find the line `DISCORD_TOKEN=` and paste your token after the `=`.
- Save and exit: press `Ctrl+O`, then `Enter`, then `Ctrl+X`.

### Step 7 — Test that it runs
```
python bot.py
```
If the bot comes online in Discord, it works! Press `Ctrl+C` to stop it for now (next step makes it run permanently).

### Step 8 — Keep it running forever (systemd service)
Right now the bot stops when you close the window. A **systemd service** makes the server run it automatically, restart it if it crashes, and start it again if the server reboots.

1. Find your folder's full path (copy what this prints):
   ```
   pwd
   ```
   It will be something like `/home/ubuntu/sprite-trade-stop`.

2. Create the service file:
   ```
   sudo nano /etc/systemd/system/sprite-trade-stop.service
   ```

3. Paste this in (if your path from `pwd` is different, change `/home/ubuntu/sprite-trade-stop` everywhere below):
   ```ini
   [Unit]
   Description=Sprite Trade Stop Discord Bot
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/sprite-trade-stop
   ExecStart=/home/ubuntu/sprite-trade-stop/.venv/bin/python /home/ubuntu/sprite-trade-stop/bot.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
   Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`.

4. Turn it on:
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable --now sprite-trade-stop
   ```

5. Check it's running:
   ```
   systemctl status sprite-trade-stop
   ```
   Look for green **active (running)**. Press `q` to exit that view.

**That's it — the bot now runs 24/7 and restarts itself automatically.** You can close the terminal and shut off your own computer; the server keeps going.

#### Handy commands later
- See live logs: `journalctl -u sprite-trade-stop -f` (press `Ctrl+C` to stop watching)
- Restart the bot: `sudo systemctl restart sprite-trade-stop`
- Stop the bot: `sudo systemctl stop sprite-trade-stop`
- Update the code after a new version is pushed (or use `./update.sh`):
  ```
  cd ~/sprite-trade-stop && git pull && source .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart sprite-trade-stop
  ```

#### Simpler alternative to systemd: `tmux`
If systemd feels like too much, `tmux` keeps the bot running after you log out (but it will **not** auto-restart on crash or reboot — systemd is better for that).
```
sudo apt install -y tmux
tmux new -s bot
source ~/sprite-trade-stop/.venv/bin/activate
python ~/sprite-trade-stop/bot.py
```
Now press `Ctrl+B`, then `D` to "detach" — the bot keeps running. To come back later: `tmux attach -t bot`.

---

## A2. EASIER FREE FALLBACKS (no Linux, web panel only)

These need no terminal at all. They're less powerful and less reliable than Oracle, but much easier.

### Option A2a — Bot-Hosting.net (free)
A free host built specifically for Discord bots, with a simple web control panel.

**What the free tier gives you (verified June 2026):**
- The free "starter" server is about **256 MB RAM**, ~20% CPU, and ~1 GB storage. That's enough for this bot.
- It runs on a **"coins"** system: you claim **free coins daily** from their coin generator, and your server costs coins over time. As long as you keep claiming, it stays free and online 24/7.
- Supports **Python** (and Node.js, Java, etc.).

**Steps:**
1. Go to <https://bot-hosting.net/>, sign in with Discord, and create a free server.
2. Open the **control panel** for your server.
3. In the **Files** tab, upload your whole bot folder (drag and drop, or use SFTP). Include `bot.py`, `requirements.txt`, and the rest of the project.
4. In the **Startup** settings, set it to a **Python** bot and point it at `bot.py`. Make sure `requirements.txt` is detected so it installs the bot's packages.
5. **Set the token:** instead of an `.env` file, look for an **Environment Variables / Startup variables** box in the panel and add `DISCORD_TOKEN` with your token as the value. (If you prefer, upload a `.env` file with the token in it.)
6. Click **Start**. Watch the console for the bot coming online.
7. **Keep coins topped up** so it never runs out — claim free coins daily.

### Option A2b — Pella (pella.app, free)
Another easy bot-hosting panel.

**What the free tier gives you (verified June 2026):**
- Free hosting with limited resources, Python supported, no credit card.
- **Important limitation:** free containers are **not truly always-on**. They require **manual renewal roughly every 24 hours**. If you forget, the bot stops. Good for **testing**, but **not ideal for set-and-forget 24/7**. Paid plans remove this.

**Steps:**
1. Go to <https://www.pella.app/discord-bot-hosting>, sign in, and create a free bot server.
2. Upload your bot folder in the **Files** section (include `bot.py` and `requirements.txt`).
3. Set the runtime to **Python** and the start file to `bot.py`.
4. **Set the token** in the panel's **Environment Variables** as `DISCORD_TOKEN`, or upload a `.env` file containing it.
5. Start the server.
6. **Remember to renew the free container every ~24 hours**, or upgrade to a cheap paid plan for true 24/7.

---

# (B) PAID PATH (~$4–5/month VPS, true 24/7)

A "VPS" is your own always-on Linux server. Around **$5/month** gets you something rock-solid that you fully control. The setup is the same idea as the Oracle steps above. Two great budget choices:

### Pricing verified June 2026
- **Hetzner CX22** — about **€4.35 / month (~$4.59)**. Specs: **2 vCPU, 4 GB RAM, 40 GB NVMe disk, 20 TB traffic.** Excellent value. (<https://www.hetzner.com/cloud>)
- **DigitalOcean basic droplet** — from **$4 / month**. Cheapest is **1 vCPU, 512 MB RAM, 10 GB SSD, 500 GB transfer.** Friendliest dashboard; bumping to the ~$6 plan (1 GB RAM) gives more headroom. (<https://www.digitalocean.com/pricing/droplets>)

Either is plenty for this bot. Hetzner gives more hardware for the money; DigitalOcean is a bit easier to navigate.

## B1. Create the server

**Hetzner:**
1. Sign up at <https://www.hetzner.com/cloud> and open **Cloud Console**.
2. **New Project** → **Add Server**.
3. **Location:** pick the one nearest you. **Image:** **Ubuntu 24.04** (or 22.04). **Type:** **CX22**.
4. Under **SSH keys**, add one (see "Getting an SSH key" below) — or choose a root password if offered.
5. Name it `sprite-trade-stop` and click **Create & Buy now**.
6. Copy the server's **IP address**.

**DigitalOcean:**
1. Sign up at <https://www.digitalocean.com> → **Create → Droplets**.
2. **Region:** nearest you. **Image:** **Ubuntu 24.04 (LTS)** or 22.04.
3. **Droplet type:** **Basic**. **CPU:** Regular, choose the **$4** or **$6/month** size.
4. **Authentication:** **SSH Key** (recommended) or password.
5. Hostname `sprite-trade-stop` → **Create Droplet**. Copy the **IP address**.

**Getting an SSH key (if you don't have one):**
- **Mac/Windows:** open Terminal/PowerShell and run `ssh-keygen` (press Enter through the prompts). Then run `cat ~/.ssh/id_ed25519.pub` (Mac) or `type $env:USERPROFILE\.ssh\id_ed25519.pub` (Windows) and paste that output into the host's "SSH key" box.

## B2. Connect (SSH)
On a paid VPS you usually log in as `root`:
```
ssh root@YOUR.IP.ADDRESS
```
Type `yes` the first time. (If you set a password instead of a key, it will ask for it.)

## B3. Install tools, get the bot, configure
```
apt update && apt upgrade -y
apt install -y python3-venv python3-pip git
git clone <repo-url> && cd sprite-trade-stop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env       # paste your DISCORD_TOKEN after the = , then Ctrl+O, Enter, Ctrl+X
python bot.py   # quick test — Ctrl+C to stop once it's online
```

> Tip: it's safer to run the bot as a non-root user, but root works fine to get started. If you used `root`, the path in the service file below is `/root/sprite-trade-stop` and `User=root`.

## B4. Run it as a service (auto-restart, 24/7)
1. Confirm your folder path: `pwd` (likely `/root/sprite-trade-stop`).
2. Create the service file:
   ```
   nano /etc/systemd/system/sprite-trade-stop.service
   ```
3. Paste this (adjust the path if `pwd` showed something different):
   ```ini
   [Unit]
   Description=Sprite Trade Stop Discord Bot
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/sprite-trade-stop
   ExecStart=/root/sprite-trade-stop/.venv/bin/python /root/sprite-trade-stop/bot.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
   Save: `Ctrl+O`, `Enter`, `Ctrl+X`.
4. Enable and start it:
   ```
   systemctl daemon-reload
   systemctl enable --now sprite-trade-stop
   ```
5. Check status:
   ```
   systemctl status sprite-trade-stop
   ```
   Green **active (running)** means you're done. Press `q` to exit.

---

## Keep it running / auto-restart (summary)

The magic line in the service file is **`Restart=always`** — if the bot ever crashes, systemd starts it again within 5 seconds. **`WantedBy=multi-user.target`** plus `enable` means it also starts automatically if the whole server reboots. So once the service is enabled:

- The bot runs 24/7.
- It restarts itself on crashes.
- It comes back after a reboot.
- You can turn off your own computer — the server is independent.

---

## Backing up the database

The bot stores everything in a single SQLite file (`sprite_trade_stop.db` inside the project folder). To keep a backup, just copy that file somewhere safe now and then. From your own computer:
```
scp -i YOUR-KEY ubuntu@YOUR.IP.ADDRESS:/home/ubuntu/sprite-trade-stop/*.db ./backups/
```
(On a Hetzner/DO root server, use `root@` and `/root/sprite-trade-stop/`.)

---

## About these prices — please double-check

All free tiers, specs, and prices in this guide were **verified on June 8, 2026** against the providers' official pages. **Cloud prices and free-tier limits change often.** Before you commit, **open the live pages and confirm the current numbers yourself**:

- Oracle Cloud Free Tier — <https://www.oracle.com/cloud/free/>
- Oracle Always Free resource limits — <https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm>
- Bot-Hosting.net — <https://bot-hosting.net/>
- Pella — <https://www.pella.app/discord-bot-hosting>
- Hetzner Cloud pricing — <https://www.hetzner.com/cloud>
- DigitalOcean Droplet pricing — <https://www.digitalocean.com/pricing/droplets>

If a price or limit looks different from what's written here, **trust the live page** — it's newer than this guide.
