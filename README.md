# Chronograph

A branching task timeline. The main horizontal axis is real time; each task you do for someone gets its own coloured branch with event nodes for each piece of work, links to SharePoint, notes, and time-taken.

Built with Streamlit + a hand-rolled SVG canvas. Data lives in a Google Sheet so the whole team sees the same picture and you don't have to email JSON files around.

## Features

- **Branching timeline** — each task is a horizontal "shelf" stacked above or below the main axis, with sphere nodes for individual events
- **In-canvas editing** — click any event node to view, edit, or delete it; click the `+` at the end of a shelf to add an event
- **Semantic zoom** — Ctrl+scroll to zoom between years / quarters / months / weeks / days; the bottom scale relabels itself
- **Pan** — click-drag the canvas
- **Today marker** — gold vertical line on the axis
- **Google Sheet backend** — data is the same for everyone on the team; Pull to refresh, Push to save
- **Local fallback** — if no sheet is configured, a local `timeline_data.json` is used

## Quick start (local, file-only mode)

```
pip install -r requirements.txt
streamlit run app.py
```

This works out of the box with no setup. Data is saved to `timeline_data.json` in the project folder. The sync strip at the top will say `LOCAL ONLY` and the Pull/Push buttons will be disabled.

## Setting up Google Sheets (one-time)

This takes about 10 minutes. You only have to do it once for the whole team.

### 1. Create a Google Cloud project

- Go to <https://console.cloud.google.com/>
- Top bar → project dropdown → **New Project** → give it a name like `chronograph` → **Create**
- Make sure that project is selected in the top bar

### 2. Enable the two APIs you need

- Search bar → "Google Sheets API" → click the result → **Enable**
- Search bar → "Google Drive API" → click the result → **Enable**

(You need both. Sheets API alone is not enough for `gspread` to open the spreadsheet by URL.)

### 3. Create a service account

A service account is a non-human Google identity that your app uses to read/write the sheet.

- Left menu → **IAM & Admin** → **Service Accounts** → **Create service account**
- Name: anything (e.g. `chronograph-app`) → **Create and continue**
- Skip the "grant access" step → **Done**
- You'll be back on the service accounts list. Click your new account.
- **Keys** tab → **Add Key** → **Create new key** → **JSON** → **Create**
- A JSON file downloads. Keep it safe — this is the credential.
- Note the service account's email address — it looks like `chronograph-app@your-project.iam.gserviceaccount.com`. You'll need it in the next step.

### 4. Create the Google Sheet and share it with the service account

- Go to <https://sheets.google.com/> → blank sheet
- Rename it (e.g. "Chronograph Timeline")
- Click **Share** in the top right
- Paste the service account email from step 3
- Permission: **Editor**
- Untick "Notify people" → **Share**
- Copy the URL of the sheet from your browser bar — you'll need it in the next step

You don't need to add any worksheets or columns yourself. The app will create them automatically the first time it writes.

### 5. Tell the app about your credentials

In the project folder, create a file at `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "chronograph-app@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"

[gsheet]
spreadsheet_url = "https://docs.google.com/spreadsheets/d/.../edit"
```

The values for the `[gcp_service_account]` block come straight from the JSON key file you downloaded in step 3 — just copy each field across. The `private_key` value will have literal `\n` characters in the JSON; keep them as `\n` in the TOML inside the triple/double-quoted string.

There's a working template at `.streamlit/secrets.toml.example` — copy it to `secrets.toml` and fill in your values.

**Don't commit `secrets.toml` to git.** There's already a `.gitignore` entry for `.streamlit/secrets.toml`.

### 6. Run it

```
streamlit run app.py
```

The sync strip should now say `● GOOGLE SHEET` in green. Push your first changes and check the sheet — you'll see two tabs (`branches` and `events`) get auto-created with the right column headers.

## Deploying to Streamlit Community Cloud

1. Push the project to GitHub (without `secrets.toml`)
2. Go to <https://share.streamlit.io/> and connect your repo
3. In the deployed app's settings, click **Advanced** → **Secrets** and paste the same content as your local `secrets.toml`
4. Reboot the app

Everyone on your team can use the same URL. They all see the same data because they're all reading the same Google Sheet.

## How sync works

- **On page load:** the app reads from the sheet (cached for 60 s) and renders the canvas. If localStorage on your browser has unsaved local edits, those win — your changes won't be wiped just because someone clicked something on the page.
- **Editing in the canvas** (clicking event dots, adding new branches/events, etc.) updates browser localStorage instantly. **Nothing is on the sheet yet.**
- **Click ☁ Push to Sheet** — pushes your current local state to the Google Sheet. Everyone else sees it after they Pull (or wait for their cache to expire).
- **Click ↻ Pull from Sheet** — discards any unsaved local edits and refreshes from the sheet. Use this when you want to see what teammates have done.

### Multi-user safety

The model is **last-write-wins**. If two people edit at once and both Push, the second Push overwrites the first. For a small team where work-in-progress is generally not overlapping, this is fine. If you want to be safe, Pull before you Push.

## Architecture

```
app.py            Streamlit shell + the SVG canvas (HTML/JS) embedded via st.components
data_layer.py     All the Google Sheets I/O, with file fallback
requirements.txt  streamlit, gspread, google-auth, streamlit-js-eval
.streamlit/
  secrets.toml    your private credentials (not in git)
timeline_data.json  fallback storage when no sheet is configured
```

The canvas talks to Streamlit through `localStorage`:
- Streamlit reads from sheet, passes JSON into the canvas via an f-string substitution
- Canvas saves edits to `localStorage['chronograph_v2']` instantly
- When you click Push, Streamlit uses `streamlit-js-eval` to read that localStorage value, then writes it to the sheet

The reason for that round-trip is that the canvas runs inside an iframe sandbox; it can't reach Streamlit's Python directly, so localStorage is the bridge.
