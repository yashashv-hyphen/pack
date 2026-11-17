# 💖 CLAT Best-Wishes Website: Setup (all free)

The website is the single file `docs/index.html`. You only need to do 3 things.

## Step 1: Personalise (1 min)
Open `docs/index.html`. Near the top is a `CONFIG` block:
```js
herName: "Anshika",   // ← already set
yourName: "Yashashv", // ← already set
```
You can also edit the letter, the notes, the jar messages and the checklist
(`LETTER`, `NOTES`, `JAR`, `CHECKLIST` near the top of the second `<script>`).

## Step 2: Get notifications on your phone (2 min, no signup)
1. Install the free **ntfy** app (Play Store / App Store).
2. Tap **+** → *Subscribe to topic* → enter exactly:
   **`clat-wishes-c9514f724ef73a12`**   (server: the default, ntfy.sh)
3. That's it. You'll get a push notification when she:
   - 👀 opens the website (and on which visit, from which device)
   - 💌 opens the envelope
   - 📝 reads all the sticky notes
   - 🤗 sends you a virtual hug
   - 🥺 presses "I feel like crying" (call her!)
   - 📍 **submits her exam centre, date, times, mood and message**
   - 📊 leaves the page (how long she stayed, what she clicked, how far she scrolled)

Don't share the topic name with anyone. Whoever knows it can read the notifications.
Messages stay in the ntfy app's history on your phone.

## Step 3 (optional): permanent log in a Google Sheet
1. Create a new Google Sheet → **Extensions → Apps Script**.
2. Paste the contents of `clat-wishes-backend/google-apps-script.gs`, save.
3. **Deploy → New deployment →** type *Web app*, Execute as *Me*, Who has access *Anyone* → Deploy → copy the URL.
4. Paste that URL into `sheetWebhook: ""` in `docs/index.html`.

## Step 4: Put it online (free link)
**Option A: GitHub Pages** (the repo must be **public** on a free plan)
1. Merge this branch into `main`, or use the branch directly.
2. Go to the repo on GitHub → **Settings → Pages**.
3. Source: *Deploy from a branch*. Branch: `main` (or this branch). Folder: **`/docs`** → Save.
4. After about 1 minute your link is `https://yashashv-hyphen.github.io/pack/`. Send that to her 💌

**Option B: Netlify Drop** (works even if the repo stays private)
Go to https://app.netlify.com/drop, sign up for free, and drag the `docs` folder in.
You get a link like `https://something.netlify.app` that you can rename in Site settings.

**Tip:** open the link once yourself to test it. You'll get notifications for your own visit too,
so do it before you send it to her.
