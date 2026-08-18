import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Telegram Video Archive Bot — Setup Guide" },
      {
        name: "description",
        content:
          "Turn your private Telegram channel into a video archive: share a link, get the real video. Step-by-step setup for Instagram, TikTok, YouTube and more.",
      },
      { property: "og:title", content: "Telegram Video Archive Bot — Setup Guide" },
      {
        property: "og:description",
        content:
          "Share a video link into your Telegram channel and the bot posts the real playable video back. Docker setup guide included.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const steps: { title: string; body: React.ReactNode }[] = [
  {
    title: "Add the bot to your channel",
    body: (
      <>
        Telegram → your channel → tap the name → <b>Edit</b> → <b>Administrators</b> →{" "}
        <b>Add Administrator</b> → select your bot.
      </>
    ),
  },
  {
    title: "Give it two permissions",
    body: (
      <>
        Turn on <b>Post Messages</b> and <b>Delete Messages</b>. Nothing else is needed.
      </>
    ),
  },
  {
    title: "Deploy on a small Ubuntu server",
    body: (
      <>
        Connect with <Code>ssh root@YOUR_SERVER_IP</Code>, then install Docker:
        <Code block>
          apt update && apt install -y docker.io docker-compose-v2 git nano && systemctl
          enable --now docker
        </Code>
      </>
    ),
  },
  {
    title: "Paste your BOT_TOKEN",
    body: (
      <>
        In the <Code>bot</Code> folder run <Code>cp .env.example .env</Code>, then{" "}
        <Code>nano .env</Code> and fill in your token and a dashboard password. Start it
        with <Code>docker compose up -d</Code>.
      </>
    ),
  },
  {
    title: "Find your Channel ID",
    body: (
      <>
        Post any message in the channel, open <Code>http://YOUR_SERVER_IP:8080</Code>, copy
        the Channel ID shown on the dashboard into <Code>ALLOWED_CHANNEL_ID</Code>, then run{" "}
        <Code>docker compose up -d</Code> again.
      </>
    ),
  },
  {
    title: "Test with an Instagram Reel",
    body: (
      <>
        Share a Reel into your channel. Within seconds the real video appears and your link
        post disappears.
      </>
    ),
  },
];

const sources = [
  "Instagram",
  "Instagram Reels",
  "TikTok",
  "YouTube",
  "YouTube Shorts",
  "X / Twitter",
  "Facebook",
  "Vimeo",
  "Reddit",
  "+ everything yt-dlp supports",
];

function Code({ children, block }: { children: React.ReactNode; block?: boolean }) {
  const cls =
    "rounded-md border border-border bg-muted px-2 py-1 font-mono text-[0.82em] text-foreground";
  return block ? (
    <pre className={`${cls} mt-3 overflow-x-auto whitespace-pre-wrap p-3`}>{children}</pre>
  ) : (
    <code className={cls}>{children}</code>
  );
}

function Index() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-3xl px-6 py-16">
        <header>
          <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
            Personal video archive
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
            Telegram Video Archive Bot
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Share a video link into your private Telegram channel. The bot downloads the real
            video, posts it back as a playable file, and deletes the link. No commands, no
            interaction.
          </p>
        </header>

        <section className="mt-12 rounded-xl border border-border bg-card p-6">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            The full bot lives in this repository
          </h2>
          <p className="mt-3 text-muted-foreground">
            Python 3.12 · aiogram 3 · yt-dlp · FFmpeg · SQLite · FastAPI dashboard · Docker.
            Everything is in the <Code>bot/</Code> folder, with the beginner guide in{" "}
            <Code>bot/SETUP - START HERE.md</Code>.
          </p>
          <p className="mt-3 text-muted-foreground">
            It runs 24/7 and writes video files to disk, so it needs Docker on a small Ubuntu
            server — a web host cannot run this kind of long-lived downloader reliably.
          </p>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold">Supported sources</h2>
          <ul className="mt-4 flex flex-wrap gap-2">
            {sources.map((source) => (
              <li
                key={source}
                className="rounded-full border border-border bg-secondary px-3 py-1 text-sm text-secondary-foreground"
              >
                {source}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-12">
          <h2 className="text-xl font-semibold">What you need to do</h2>
          <ol className="mt-6 space-y-6">
            {steps.map((step, index) => (
              <li key={step.title} className="flex gap-4">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                  {index + 1}
                </span>
                <div>
                  <h3 className="font-medium">{step.title}</h3>
                  <div className="mt-1 text-muted-foreground">{step.body}</div>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-12 rounded-xl border border-border bg-card p-6">
          <h2 className="text-xl font-semibold">Built in</h2>
          <ul className="mt-4 grid gap-2 text-muted-foreground sm:grid-cols-2">
            <li>Only listens to your one channel</li>
            <li>Duplicate detection with SQLite</li>
            <li>Queue limited to 2 downloads at a time</li>
            <li>Retries and download timeouts</li>
            <li>Automatic temp-file cleanup</li>
            <li>Friendly error messages in the channel</li>
            <li>Password-protected dashboard</li>
            <li>Token never logged or displayed</li>
          </ul>
        </section>

        <footer className="mt-16 border-t border-border pt-6 text-sm text-muted-foreground">
          Open <Code>bot/SETUP - START HERE.md</Code> for the full copy-paste guide.
        </footer>
      </div>
    </div>
  );
}
