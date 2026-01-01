# Deploying StayOnTrack with Render + Supabase (Free Forever*)

You have chosen the **Smart Architecture**: Hosting the app on **Render** (Free Web Service) and the database on **Supabase** (Free Postgres) to avoid the 90-day data deletion limit.

## Phase 1: Get Your Free Database (Supabase)
1.  Go to [supabase.com](https://supabase.com/) and click **"Start your project"**.
2.  Sign in with GitHub.
3.  Click **"New Project"**.
4.  **Name**: `StayOnTrack-DB`.
5.  **Password**: Generata a strong password and **COPY IT NOW** (you won't see it again).
6.  **Region**: Choose one close to you (e.g., Mumbai, Singapore, US East).
7.  Click **"Create new project"**.
8.  Wait ~2 minutes for the database to build.
9.  Once ready, go to **Project Settings (Cog Icon)** -> **Database**.
10. Scroll to **Connection parameters** or **Connection String**.
11. Click **URI** tab. It will look like:
    `postgresql://postgres.xxxx:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres`
    *   **Important**: Replace `[YOUR-PASSWORD]` with the real password you created in step 5.
    *   **Copy this entire string**. This is your `DATABASE_URL`.

## Phase 2: Deploy App on Render
1.  Push your code to GitHub (if not already done).
2.  Go to [dashboard.render.com](https://dashboard.render.com/).
3.  Click **"New"** -> **"Blueprint Preview"**.
4.  Connect your GitHub repository.
5.  Render will load `render.yaml`.
6.  It will ask for `DATABASE_URL`. **Paste the Supabase connection string you copied above.**
7.  Click **"Apply"**.

## Phase 3: Verify
*   Render will deploy your app.
*   The first time the app starts, it will automatically connect to Supabase and create all your tables (`init_db` logic in code).
*   **Result**: You now have a persistent, free-forever database for your student records!

*Note: Supabase pauses projects after 7 days of inactivity. To wake it up, just log in to the Supabase dashboard once.*
