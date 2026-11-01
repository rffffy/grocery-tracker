# Google Drive OAuth — n8n

## What is OAuth and how does this work?

OAuth lets n8n access your Google Drive without you sharing your Google password. Instead of a password, Google issues a short-lived **access token** that n8n uses to make Drive API calls. When the token expires (usually after 1 hour), n8n silently refreshes it using a long-lived **refresh token** stored in the `n8n_data` Docker volume. You never have to log in again unless something breaks.

The chain looks like this:

```
Google Cloud project (grocery-tracker)
  └── OAuth app (Client ID + Client Secret)
        └── User consented → Google issued refresh token to n8n
              └── n8n stores token in n8n_data Docker volume
                    └── n8n uses token to call Google Drive API
```

## What you set up

| Piece | Where it lives |
|-------|---------------|
| Google Cloud project | console.cloud.google.com → project `grocery-tracker` |
| OAuth Client ID + Secret | Google Cloud Console → APIs & Services → Credentials |
| Refresh token | Encrypted inside the `n8n_data` Docker volume |
| n8n credential | n8n → Personal → Credentials → `Google Drive` |

---

## Day-to-day

Nothing to do. The token refreshes automatically in the background. The credential just works as long as:
- n8n is running
- You haven't revoked access in your Google Account
- The Client ID / Secret haven't been deleted or changed in Google Cloud

---

## If the connection breaks

Go to **n8n → Personal → Credentials → Google Drive** → click **Sign in with Google** again. This issues a fresh token without needing to touch Google Cloud Console.

---

## How to revoke access (stop n8n from accessing Drive)

Do both steps:

**1. Revoke in your Google Account**
- Go to myaccount.google.com → **Security** → **Third-party apps with account access**
- Find **Grocery Tracker** → click it → **Remove access**

This immediately invalidates the refresh token stored in n8n. The workflow will fail at the Drive step until you reconnect.

**2. (Optional) Delete the Google Cloud project**
- Go to console.cloud.google.com → select project `grocery-tracker`
- Click the three-dot menu → **Project settings** → **Shut down** (or search for "Manage resources")
- This destroys the Client ID and Client Secret permanently

Only do step 2 if you're done with the project entirely. If you want to reconnect later, you'd have to recreate the OAuth app.

---

## How to update the Client Secret

If you regenerate the Client Secret in Google Cloud Console (e.g. for security rotation):

1. Copy the new secret from Google Cloud Console → APIs & Services → Credentials → your OAuth client
2. In n8n: **Personal → Credentials → Google Drive** → paste the new **Client Secret**
3. Click **Sign in with Google** again to issue a new refresh token

---

## Security notes

- The Client ID and Client Secret are entered into the n8n credential. A copy can be kept in `.env` (`GOOGLE_DRIVE_CLIENT_ID` / `GOOGLE_DRIVE_CLIENT_SECRET`), which is git-ignored, so never commit it
- The `n8n_data` Docker volume contains the encrypted refresh token — don't share or expose the volume
- The OAuth app is in **testing mode** — only your Google account can authenticate with it, so no one else can grant access even if they have the Client ID
- n8n only accesses Drive when a workflow node explicitly calls the Drive API — there is no background scanning of your Drive

---

## Quick reference

| Task | Where |
|------|-------|
| Reconnect after token expiry | n8n → Credentials → Google Drive → Sign in with Google |
| Revoke all access | myaccount.google.com → Security → Third-party apps |
| View/edit the OAuth app | console.cloud.google.com → project `grocery-tracker` → APIs & Services → Credentials |
| Add another test user | Google Cloud Console → Google Auth Platform → Audience → Test users |
| Delete the OAuth app entirely | Google Cloud Console → APIs & Services → Credentials → delete the OAuth client |
