# Deploy & run (backend, tunnel, GitHub Pages)

## 1. Push to GitHub

From **Command Prompt** or **PowerShell** (in `C:\Users\Akhil\locator`):

```bat
git push origin main
```

If you use 2FA, use a **Personal Access Token** as password when prompted.

---

## 2. Start the backend

**First-time setup** (if `backend\.venv` does not exist):

```bat
cd C:\Users\Akhil\locator\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed_db.py
```

**Run the backend:**

```bat
cd C:\Users\Akhil\locator
start-backend.bat
```

Or manually:

```bat
cd C:\Users\Akhil\locator\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this window open. Backend runs at **http://localhost:8000**.

---

## 3. Start Cloudflare Tunnel

Open a **second** Command Prompt window:

```bat
cd C:\Users\Akhil\locator
start-tunnel.bat
```

Or run:

```bat
cloudflared tunnel --url http://127.0.0.1:8000
```

A **tunnel URL** (e.g. `https://xxxx-xx-xx-xx-xx.trycloudflare.com`) will appear. Use this URL as the **Server URL** in the driver app and, if needed, update the API base URL in admin/passenger (see your setup).

---

## 4. Admin & passenger (GitHub Pages)

The `docs` folder is set up for **GitHub Pages**:

- **Repo** → **Settings** → **Pages**
- **Source**: Deploy from a branch
- **Branch**: `main` (or your default)  
- **Folder**: `/docs`
- **Save**

After you **push** (step 1), the site updates automatically.

- **Site URL**: `https://<your-username>.github.io/locator/`
- **Admin**: `https://<your-username>.github.io/locator/admin/`
- **Passenger**: `https://<your-username>.github.io/locator/passenger/`

Admin and passenger use a configurable API base URL (or localStorage). Point them at your **tunnel URL** (from step 3) when testing.

---

## Quick checklist

1. `git push origin main`
2. Run `start-backend.bat` (ensure `backend\.venv` exists).
3. Run `start-tunnel.bat` in another window; note the tunnel URL.
4. Confirm **GitHub Pages** uses **`/docs`** on **`main`**.
5. Open admin/passenger from the Pages URL; use the tunnel URL as the API base where configured.
