# Workovia — deploy package (22 Oct 2026)

## Deploy via GitHub -> Netlify (recommended)
Every file is now under GitHub's 100 MB limit (both Dawat menu PDFs were rebuilt: 148 MB -> 10 MB, 55 MB -> 7 MB).
1. Create a PRIVATE repo on github.com (e.g. workovia-site). Do NOT add a README/.gitignore there.
2. In this folder (GitHub Desktop or terminal):
     git init
     git add .
     git commit -m "Workovia site"
     git branch -M main
     git remote add origin https://github.com/<you>/workovia-site.git
     git push -u origin main
3. Netlify -> Add new site -> Import an existing project -> GitHub -> pick the repo.
     Build command: (leave empty)      Publish directory: .      (netlify.toml already says publish = ".")
4. Netlify -> Domain management -> add workovia.in (move the domain from the old drag-drop site, or delete that site).
5. Netlify -> Forms -> Form notifications -> Email (see below).
From then on: edit -> commit -> push = live in ~1 minute, with rollback in Deploys.


Domain used everywhere: https://workovia.in (index.html, sitemap.xml, robots.txt)

## Careers page videos (placeholders are live until you add the files)
Drop your two MP4s here and nothing else needs changing:
  videos/careers-who.mp4   -> first blue section ("Who it's for")
  videos/careers-how.mp4   -> second blue section ("How it works")
They autoplay muted, loop, 16:9. Until the files exist the blue "Video" placeholder shows.

## What changed in this build
- Scroll film: 420 frames (60 per scene) from the original film. frames/d = 1280x720 desktop/tablet,
  frames/m = 720x1080 portrait for phones. Smoother film chase, slow-network thinning.
- Careers page: Workovia look (Inter, blue), roles directly in the hero, two blue video sections, site footer.
- Our Process page: site footer added; stray </div> fixed (it was pushing a 174px strip below the home footer).
- SEO: brand-first title/description, canonical + og:url, images/og-workovia.png, JSON-LD (Organization,
  WebSite, Services, JobPostings, FAQ), static crawlable service cards, sitemap.xml, robots.txt,
  Netlify clean URLs: /careers /process /services /contact.

## Lead form + job application form = Netlify Forms (no backend needed)
Both forms POST to Netlify ("project-scope" and "job-application"). After the first deploy:
  Netlify -> Site -> Forms -> you will see both forms and every submission.
  Forms -> Form notifications -> Add notification -> Email -> your inbox (do this once, else leads only sit in the dashboard).
Free tier: 100 submissions/month. If a POST ever fails, the user gets a mailto fallback to careers@workovia.cloud.

## After upload
1. Google Search Console -> add workovia.in -> submit https://workovia.in/sitemap.xml -> Request indexing for /.
2. Send the brand's Instagram / LinkedIn / YouTube URLs for the Organization "sameAs" (strongest signal
   against the "Workiva" autocorrect).
3. Confirm the careers inbox (index.html uses careers@workovia.cloud from the old build).

## Rebuilding frames later
Frames are cached by browsers for a year (immutable). After ANY new frame build, bump FRAME_VER in index.html
(search: const FRAME_VER) so every visitor fetches the new files instead of the cached old ones.
python3 tools/make_frames.py <film.mp4> --per-scene 60 --quality 74
