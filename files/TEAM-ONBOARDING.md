# 👋 Welcome to Our Hackathon Project!

**A friendly guide for the team — no experience needed.**

Hey team! This document explains everything you need to know about how we're going to work together during the hackathon. Don't worry if you're new to Git or this kind of project setup — by the end of this doc, you'll understand exactly what's going on. Take your time reading it, and feel free to ask questions any time. 🙂

---

## 📌 First, the most important thing to know

**Everything in this repository right now is a TEMPLATE.**

We don't know our exact hackathon theme yet, so we built a generic starting structure ahead of time — just so we don't waste precious hackathon hours on setup. Once we know our theme, we'll quickly adjust folders, files, and tasks to match what we actually need to build.

So if some folder names look a little abstract right now ("processors", "api", etc.) — that's fine. Think of it like an empty toolbox we packed in advance. Once we know the job, we'll know exactly which tools to use.

---

## 🧩 What is this project, in simple terms?

No matter what theme we get, almost every hackathon challenge follows the same basic shape:

1. **We receive a dataset** (a file full of data — like a spreadsheet, a CSV, or JSON file)
2. **We process/analyze that dataset** with code (find patterns, calculate stats, run predictions, etc.)
3. **We show the results** in a nice-looking app/website so judges can see what we found

That's it. Three steps. Our whole repo is organized around these three steps.

---

## 🗂️ The Folder Structure (and what each one is for)

Here's what the project looks like right now:

```
hackathon-project/
│
├── backend/              ← All the "thinking" happens here (data processing + API)
│   ├── src/
│   │   ├── api/          ← Code that exposes our results to the app
│   │   ├── processors/   ← Code that reads & analyzes the dataset
│   │   └── models/        ← (Optional) AI/ML logic, if we need it
│   │
│   ├── data/
│   │   ├── raw/          ← Where we put the dataset file we receive
│   │   └── processed/    ← Where we put the results after analysis
│   │
│   └── server.js          ← The "engine" that runs everything
│
├── frontend/              ← The visual app the judges will see (built with Lovable)
│
├── docs/                  ← Notes & explanations about our specific theme
│
├── CLAUDE.md               ← Instructions we give to our AI assistant (Claude)
├── .gitignore               ← A list of files Git should ignore (see below)
├── README.md               ← General info about the project
└── package.json            ← List of code libraries our project needs
```

### What do these folders actually mean?

- **`backend/`** — This is where the "brain" of our project lives. It reads the dataset, crunches the numbers, and prepares answers.
- **`backend/data/raw/`** — Whatever dataset file we get from the organizers goes here. (Important: this folder is NOT uploaded to GitHub — explained below in the "datasets" section.)
- **`backend/data/processed/`** — After we analyze the raw data, the *results* get saved here.
- **`backend/src/processors/`** — This is the actual code that does the analysis. This is the part that will change the most once we know our theme.
- **`backend/src/api/`** — This is a "bridge" that lets our frontend (the website) ask the backend "hey, what did you find?" and get an answer back.
- **`frontend/`** — This will hold the actual app/website that we build using **Lovable** (an AI tool that builds websites for us based on descriptions). Judges will look at this.
- **`docs/`** — Just notes for ourselves, so we remember what we're building and why.

**Again: this is just a starting skeleton.** Folder names and contents will be refined once we get our theme and split up tasks.

---

## 👥 How are we splitting up the work?

Here's the (current just a draft version) plan for who works where:

| Person | Main Focus | Folder(s) |
|--------|-----------|-----------|
| **Pedro** | Backend & data processing — writing the code that reads the dataset and finds insights | `backend/src/api/`, `backend/src/processors/` |
| **Masha** | Frontend — building the visual app using Lovable, displaying our results nicely | `frontend/` |
| **Alisa** | Data management & testing — getting the dataset into the right place, double-checking things work, helping wherever needed | `backend/data/raw/`, general QA |
| **Dima (me)** | Team lead — repo setup, coordinating tasks, making sure everything connects together, final submission | Overall coordination |

**Important:** This split is also just a *starting point*. Once we know our theme, we'll likely adjust who does what based on the actual tasks. Nobody is locked into one folder forever — we'll talk and adapt as a team.

The general idea, though, is:
- One person focuses on the **data/backend** side (processing data, building logic)
- One person focuses on the **frontend** side (making it look good, using Lovable)
- Everyone helps with testing, debugging, and last-minute fixes

---

## 🌳 Git Basics — Don't worry, it's simpler than it looks

Git is just a tool that keeps track of all the changes we make to our code over time, like a really powerful "save history" for the whole project, and lets multiple people work on the same project without overwriting each other's work.

### The Big Idea: Branches

Think of a "branch" as a parallel version of our project. We have two:

- **`main`** — This is our **final, polished, submission-ready version**. We do NOT touch this branch until the very end of the hackathon.
- **`develop`** — This is our **everyday working version**. This is where ALL of us will work, commit changes, and collaborate throughout the day.

```
              ┌─────────────────────────────┐
              │   develop (we work here!)    │
              │   ───●────●────●────●──────  │
              │      ↑     ↑    ↑    ↑       │
              │    Pedro  Alisa Masha Dima   │
              └─────────────────────────────┘
                              │
                    (at the very end)
                              ▼
              ┌─────────────────────────────┐
              │   main (final version)       │
              │   ────────────────────●──────│
              └─────────────────────────────┘
```

Why two branches? Because if everyone worked directly on `main`, one small mistake could break our final submission. By working on `develop` instead, we can experiment, make mistakes, and fix them — without any risk to the version we'll actually submit. At the very end of the day, we merge `develop` into `main` once everything works.

### How do I get my changes onto our shared project?

Every time you finish writing some code (a "chunk" of work, like a feature or a fix), you'll do these steps:

```bash
git add .                          # Step 1: "Stage" your changes (mark them as ready)
git commit -m "what you did"       # Step 2: Save a snapshot with a short description
git push origin develop            # Step 3: Upload your snapshot to GitHub for everyone
```

Think of it like this:
1. `git add .` = "select all my changed files"
2. `git commit -m "..."` = "save this version with a note describing what I did" (like saving a Word document with a clear filename)
3. `git push origin develop` = "upload this save to the shared cloud folder so everyone sees it"

### How do I get everyone else's changes?

Before you start working each time, run:

```bash
git pull origin develop
```

This downloads everyone else's latest work onto your computer, so you're never working on an outdated version. **Always do this first thing when you sit down to work.**

### Quick Daily Routine (memorize this!)

```bash
# 1. When you start working:
git checkout develop
git pull origin develop

# 2. While you work, make your changes...

# 3. When you finish a piece of work:
git add .
git commit -m "short description of what you did"
git push origin develop
```

That's really it. Those are the only commands you'll use 95% of the time.

### What if two people changed the same file?

Occasionally, Git might tell you there's a "conflict" — this just means two people edited the exact same lines of a file. Don't panic if this happens! It's normal and easy to fix. Just ask Dima for help, and we'll walk through it together. To avoid this happening often, we're each working in our own folder, so it shouldn't come up much.

---

## 📊 A note about datasets (the actual data files)

Whatever dataset(s) the organizers give us will likely be **large files** (sometimes hundreds of megabytes). GitHub isn't really built for storing huge files like that, so:

- ✅ We will put dataset files in `backend/data/raw/` **on our own computers** (locally)
- ❌ We will **NOT** upload these dataset files to GitHub
- 📤 Instead, we'll share the dataset with each other via something like Google Drive or Slack

There's a file in our repo called `.gitignore` that tells Git "please ignore these files, don't upload them" — so even if you accidentally try to commit a dataset file, Git will skip it automatically. No need to worry about doing this wrong — it's already set up for you.

---

## 🛠️ What is "Lovable" and why are we using it?

**Lovable** is a tool where you describe what you want a website/app to look like in plain English, and it generates the actual code for you using AI. Masha will use this to build our frontend (the visual part judges will see), instead of writing all the React/HTML code by hand. This saves us a ton of time during the hackathon.

The frontend (built in Lovable) will talk to our backend (Pedro's code) to get the actual results/data to display. So the workflow looks like:

```
Dataset → Pedro's backend code analyzes it → Masha's frontend (Lovable) displays it nicely
```

---

## 🤖 What is "Claude Code" and why do we have a `CLAUDE.md` file?

We're using an AI coding assistant called **Claude Code** to help us write code faster during the hackathon. The `CLAUDE.md` file in our repo is basically a set of instructions we give to this AI assistant, so it understands:

- What our project is about
- What rules to follow (like "don't touch the main branch")
- What coding style we want
- Who's responsible for which folder

You don't need to memorize this file — it's mostly there to help the AI assistant help *us* better. But feel free to skim it if you're curious.

---

## ❓ "I'm nervous, what if I break something?"

Totally normal feeling, and here's the good news:

1. **You can't break `main`** — that branch is protected and we only touch it at the very end, together.
2. **Git remembers everything** — even if you mess something up on `develop`, we can always go back to an earlier saved version. Nothing is ever truly lost.
3. **You're not alone** — if you're stuck or confused at any point, just ask in the group chat. We'll sort it out together, no judgment.
4. **Mistakes are part of the process** — every developer, even very experienced ones, hits errors and conflicts regularly. It's normal, not a sign you're doing something wrong.

---

## 📅 What happens once we know our theme?

On the morning of the hackathon, once the actual challenge/theme is announced:

1. Dima will quickly update a file called `docs/THEME_SPECIFIC.md` with details about what we're actually building
2. We'll have a short team huddle to assign more specific tasks based on the real challenge
3. Pedro will start adjusting the `backend/src/processors/` code to handle our actual dataset
4. Alisa will start building the actual app screens in Lovable based on what we need to show
5. Masha will grab the dataset file from the organizers and drop it into `backend/data/raw/` (locally, not on GitHub)

This whole adjustment should take maybe 15–20 minutes, and then we're off to the races. 🚀

---

## ✅ Quick Cheat Sheet (keep this open during the hackathon)

```bash
# Clone the project (only once, at the very start)
git clone [REPO_LINK]
cd hackathon-project
git checkout develop

# Every time you start working
git pull origin develop

# Every time you finish a piece of work
git add .
git commit -m "describe what you did"
git push origin develop
```

| Term | What it means |
|------|---------------|
| **Repository (repo)** | The whole project folder, tracked by Git |
| **Branch** | A parallel "version" of the project (we have `main` and `develop`) |
| **Commit** | A saved snapshot of your changes, with a short description |
| **Push** | Uploading your saved snapshot to GitHub (the shared cloud) |
| **Pull** | Downloading everyone else's latest snapshots onto your computer |
| **Merge** | Combining changes from one branch into another (we'll do this at the end: develop → main) |

---

## 🙌 Final note

This document — and the whole repo, really — is meant to make our lives *easier*, not harder. If anything here feels confusing, that's a sign we should explain it better, not that you're missing something obvious. Ask questions whenever you need to. We're a team, and we'll figure this out together.

**See you at the hackathon!** 🎉