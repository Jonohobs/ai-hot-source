# Automated Content + Marketing Pipeline for Auckland Plumber

**Date:** 2026-03-21
**Status:** Design / Research Complete
**Stack:** n8n (Hetzner VPS) + Claude API + Remotion + Meta Graph API + ServiceM8

---

## Architecture Overview

```
Steve's Phone (photo/job complete)
    |
    v
Google Drive / Dropbox sync
    |
    v
n8n (Hetzner VPS @ 178.104.85.59)
    |--- Claude API --> caption + hashtags
    |--- Meta Graph API --> Facebook + Instagram
    |--- GBP API --> Google Business Profile post
    |--- Twilio/Sinch --> SMS review request
    |--- Remotion (render server) --> video content
    |--- YouTube Data API --> Shorts upload
    |--- ServiceM8 webhooks --> job lifecycle triggers
```

---

## Component 1: Automated Social Posting

### How It Works
1. Steve finishes a job, takes a photo on his iPhone
2. Photo auto-uploads to a Google Drive folder (native iOS/Android sync)
3. n8n watches the Google Drive folder (polling every 5 min)
4. On new photo detected:
   - n8n sends image to Claude API (vision) with prompt:
     ```
     You are a social media manager for Steve's Plumbing, Auckland.
     Write a Facebook/Instagram caption for this completed job photo.
     Include: what was done, professional tone but friendly,
     2-3 relevant hashtags (#AucklandPlumber #PlumbingNZ etc).
     Keep under 200 words.
     ```
   - Claude returns caption + hashtags
   - n8n posts to Facebook Page via Graph API
   - n8n posts to Instagram Business via Graph API (requires image URL accessible from internet -- Google Drive public link or re-upload to hosting)
5. Weekly cron (Monday 9am NZST): Claude picks a tip from content bank Google Sheet, generates post

### Feasibility: HIGH
- n8n has native Google Drive trigger + Facebook Graph API nodes
- Pre-built template exists: [n8n workflow #3478](https://n8n.io/workflows/3478-automate-instagram-posts-with-google-drive-ai-captions-and-facebook-api/)
- Instagram requires Business account linked to Facebook Page (free)
- Meta Graph API allows 50 posts/24hr (more than enough)
- Claude vision can describe plumbing work accurately

### Requirements
- Facebook Page for the business
- Instagram Business account linked to Facebook Page
- Meta Developer App (free) with `pages_manage_posts` and `instagram_content_publish` permissions
- Google Drive folder designated for job photos
- Claude API key

### Monthly Cost
| Item | Cost |
|------|------|
| Claude API (vision, ~30 photos/mo + 4 tips) | ~$2-4 USD |
| Meta Graph API | Free |
| Google Drive | Free (15GB) |
| n8n (already running on Hetzner) | $0 incremental |
| **Total** | **~$3/month** |

### Build Effort: 4-6 hours
- 2hr: Meta Developer App setup + OAuth flow
- 1hr: n8n workflow (Google Drive trigger -> Claude -> FB/IG post)
- 1hr: Weekly tip-of-the-week cron workflow
- 1hr: Testing + Steve onboarding

---

## Component 2: Review Solicitation Automation

### How It Works
1. Steve marks job as "Complete" in ServiceM8 (or manual trigger via n8n form)
2. ServiceM8 webhook fires to n8n
3. n8n waits 2 hours (let Steve leave the property)
4. Sends SMS: "Hi [name], thanks for choosing Steve's Plumbing! If you were happy with the work, a Google review would mean the world: [short link]. Cheers, Steve"
5. If no review detected after 3 days, send polite follow-up SMS
6. If no review after 7 days, send email (softer ask)

### NZ SMS Providers (Researched)

| Provider | NZ Price/SMS | NZ Numbers | n8n Integration | Notes |
|----------|-------------|------------|-----------------|-------|
| **Twilio** | ~$0.105 USD (~$0.17 NZD) | Yes (but deliverability issues with NZ-originated numbers) | Native n8n node | Most documented, largest ecosystem |
| **Sinch** (inc. MessageMedia) | ~$0.07 USD (~$0.11 NZD) | Yes | HTTP Request node | Australian company, strong in ANZ market. MessageMedia brand well-known in NZ |
| **Vonage** | ~$0.08 USD | Yes, with restrictions | Native n8n node | Some NZ number restrictions |
| **Plivo** | ~$0.07 USD | Yes | HTTP Request node | Cheapest, less NZ-specific support |

**Recommendation:** Start with **Twilio** (best n8n integration, most docs) or **Sinch/MessageMedia** (better ANZ deliverability, cheaper). For a plumber sending ~40-60 SMS/month, the cost difference is negligible.

**NZ Compliance:** Under NZ Unsolicited Electronic Messages Act 2007:
- Must have consent (job completion = existing business relationship, but explicit opt-in is safer)
- Must include opt-out mechanism
- Must identify sender
- Add a consent checkbox to the booking form: "Can we text you after the job?"

### Monthly Cost
| Item | Cost |
|------|------|
| Twilio SMS (~50 messages @ $0.105) | ~$5.25 USD |
| Twilio NZ number rental | ~$6 USD/mo |
| Follow-up SMS (~15 second messages) | ~$1.60 USD |
| ServiceM8 (Steve likely already has this) | $0 incremental |
| **Total** | **~$13/month** |

### Expected ROI
- A single 5-star Google review can be worth $50-500 in local SEO value
- Plumbers in Auckland average 3-5 reviews/month with manual asking
- Automated sequences typically get 15-25% review rate
- 50 jobs/month * 20% = 10 reviews/month = massive local SEO advantage
- **ROI: Extreme.** This is the single highest-value automation.

### Build Effort: 3-4 hours
- 1hr: Twilio account setup + NZ number
- 1hr: ServiceM8 webhook -> n8n workflow (with delay nodes)
- 1hr: Follow-up sequence logic + opt-out handling
- 30min: Google review short link setup

---

## Component 3: Quote/Booking Automation

### How It Works
1. Website contact form submits to n8n webhook
2. n8n auto-responds with email:
   - "Thanks [name], Steve's Plumbing received your enquiry about [issue]. We typically respond within 2 hours during business hours. For emergencies, call [number]."
3. n8n creates a lead/job in ServiceM8 automatically
4. n8n sends Steve a push notification (via Slack/Telegram/SMS) with the lead details
5. Optional: Claude API triages the enquiry (emergency vs routine, rough quote range)

### Job Management Integration

| Platform | API Quality | n8n Support | NZ Popularity | Monthly Cost |
|----------|------------|-------------|---------------|-------------|
| **ServiceM8** | Excellent (REST + webhooks) | Native node + official n8n plugin | Very popular in NZ/AU | $29-$379 NZD/mo |
| **Tradify** | Limited (no public API docs found) | No native node | Very popular in NZ (NZ-made) | $35-$55 NZD/user/mo |
| **Jobber** | Good (REST API) | No native node (HTTP request) | More North American | $49-$249 USD/mo |
| **Fergus** | Limited | No | NZ-made, popular with tradies | ~$40 NZD/mo |

**Recommendation:** **ServiceM8** is the clear winner for automation. It has a dedicated n8n node, webhooks, and full API. If Steve already uses Tradify (many NZ plumbers do), the automation options are limited -- we'd need to work with Tradify's Zapier integration or email-based triggers instead.

### Monthly Cost
| Item | Cost |
|------|------|
| n8n workflow | $0 incremental |
| Claude API (triage, ~50 enquiries) | ~$0.50 USD |
| ServiceM8 (if not already subscribed) | $29-99 NZD/mo |
| **Total (if already on ServiceM8)** | **~$1/month** |

### Build Effort: 3-4 hours
- 1hr: Website form -> n8n webhook setup
- 1hr: Auto-response email template + ServiceM8 job creation
- 1hr: Steve notification channel (Telegram bot is easiest)
- 30min: Testing

---

## Component 4: Video Content Automation

### How It Works

**Tip-of-the-Week Videos (Remotion)**
1. Content bank: Google Sheet with 52 plumbing tips (one per week)
   - "How to fix a dripping tap"
   - "Why your hot water goes cold"
   - "What to do if your toilet won't stop running"
2. n8n cron (weekly) picks next tip
3. Claude API generates script (~30 seconds of narration)
4. ElevenLabs API generates voiceover from script
5. Remotion renders video:
   - Branded template (Steve's Plumbing logo, Auckland skyline, brand colors)
   - Text overlay of key points
   - Stock footage/illustrations (pre-loaded library of ~20 plumbing clips)
   - AI voiceover audio track
   - 9:16 aspect ratio for Shorts/Reels
6. n8n uploads to YouTube Shorts + Instagram Reels + Facebook

**Feasibility Assessment:**
- Remotion CAN generate videos from text + stock footage + audio. This is its sweet spot.
- ElevenLabs free tier: 10,000 chars/month (~12 min audio). A 30-sec script is ~500 chars. 52 tips/year = ~26,000 chars total, so **free tier covers ~5 months** at one video/week.
- YouTube Data API supports upload via n8n HTTP request node
- Pre-built n8n YouTube Shorts workflows exist

**BUT -- rendering requires compute:**
- Remotion render on Hetzner VPS (ARM64, 4GB RAM): possible but slow (~2-5 min per 30sec video)
- Alternative: Remotion Lambda (AWS) -- ~$0.05/render
- Alternative: Creatomate (SaaS video API, n8n integration) -- avoids self-hosting Remotion

### Realistic Approach
For Phase 1, skip Remotion. Use **Creatomate** or **Canva API** for video generation -- they handle rendering, templates, and have n8n integrations. Remotion is better if Steve wants custom animations long-term.

For voiceover, ElevenLabs Starter plan ($5/mo, 30,000 chars) covers the full year of weekly tips comfortably.

### Monthly Cost
| Item | Cost |
|------|------|
| ElevenLabs Starter | $5 USD/mo |
| Creatomate (alt to Remotion) | $0 (free: 5 videos/mo) or $12/mo |
| Claude API (scripts) | ~$0.50 USD |
| Stock footage (Pexels/Pixabay) | Free |
| YouTube Data API | Free |
| **Total** | **$6-18/month** |

### Build Effort: 8-12 hours (most complex component)
- 3hr: Design video template (Remotion or Creatomate)
- 2hr: ElevenLabs integration
- 2hr: n8n workflow (script -> voiceover -> render -> upload)
- 2hr: Stock footage library curation
- 1hr: Content bank (52 tips in Google Sheet)
- 2hr: Testing and iteration

---

## Component 5: Local SEO Automation

### Google Business Profile Posting
- n8n has a **native GBP node** ([docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlebusinessprofile/))
- Can create posts, respond to reviews, update business info
- Pre-built workflow template: [n8n #6165](https://n8n.io/workflows/6165-automate-google-business-profile-posts-with-gpt-4-and-google-sheets/)
- **Important:** Must request GBP API quota in Google Cloud Console (default is 0)
- Automation: Every job photo posted to social also gets posted to GBP as an "update"

### Blog Post Generation for Local SEO
- Claude API generates suburb-targeted pages:
  - "Emergency Plumber in Ponsonby"
  - "Hot Water Cylinder Replacement in Mt Eden"
  - "Blocked Drain Plumber Grey Lynn"
- Each page: ~500-800 words, unique content, local landmarks/references
- Auckland has ~100+ suburbs = 100+ pages of local SEO content
- **Generate in batch**, human-review, then publish weekly
- Host on Steve's website (WordPress or static site)

### NZ Citation Building (Manual + Semi-Automated)

**Essential NZ Directories (manual submission, one-time):**

| Directory | Cost | Priority |
|-----------|------|----------|
| Google Business Profile | Free | CRITICAL |
| Yellow NZ (yellow.co.nz) | Free basic listing | HIGH |
| NoCowboys | $129/mo or $999/yr | HIGH (trades-specific, review-focused) |
| Builderscrack | Free (commission on jobs) | MEDIUM |
| Finda (finda.co.nz) | Free | MEDIUM |
| Localist (localist.co.nz) | Free | MEDIUM |
| Hotfrog NZ | Free | LOW |
| Yelp NZ | Free | LOW |
| Facebook Business Page | Free | Already have |
| Apple Maps Connect | Free | MEDIUM |

**Semi-automation:** Claude generates consistent NAP (Name, Address, Phone) listings. n8n tracks which directories Steve is listed on. Can't fully automate submissions (each directory has its own signup flow), but can automate the content generation and tracking.

### Monthly Cost
| Item | Cost |
|------|------|
| GBP API | Free |
| Claude API (blog posts, ~4/month) | ~$2 USD |
| NoCowboys (if opted in) | $129 NZD/mo |
| Other directories | Free |
| **Total (without NoCowboys)** | **~$2/month** |
| **Total (with NoCowboys)** | **~$85 USD/month** |

### Build Effort: 6-8 hours
- 2hr: GBP API setup + n8n workflow
- 2hr: Blog post generation workflow + templates
- 2hr: Manual directory submissions (one-time)
- 2hr: Blog publishing pipeline (depends on website platform)

---

## Phased Implementation Plan

### Phase 1: Free/Near-Free, 1-Day Build (~$3/month)

**Goal:** Get automated social posting working TODAY.

| Task | Time | Cost |
|------|------|------|
| Set up Google Drive folder "Job Photos" on Steve's phone | 15min | Free |
| Create Meta Developer App, get tokens | 1hr | Free |
| Build n8n workflow: Drive trigger -> Claude caption -> FB + IG post | 2hr | ~$3/mo (Claude) |
| Set up GBP API + post job photos there too | 1hr | Free |
| Create Google Sheet with 12 plumbing tips (3 months) | 30min | Free |
| Build weekly tip cron in n8n | 30min | Free |
| Test end-to-end with Steve | 30min | Free |

**Deliverables:**
- Steve takes photo -> auto-posts to Facebook, Instagram, Google Business Profile
- Weekly plumbing tip auto-posted
- Total: ~6 hours, ~$3/month

**Measurement:**
- Track: posts/week, engagement (likes/comments), profile visits
- Baseline Steve's current Google ranking for "plumber [suburb]"

---

### Phase 2: Low Cost, 1-Week Build (~$20/month)

**Goal:** Automated review collection + quote handling.

| Task | Time | Cost |
|------|------|------|
| Twilio account + NZ number | 1hr | ~$13/mo |
| ServiceM8 webhook -> n8n review request workflow | 2hr | $0 incremental |
| SMS follow-up sequence (2hr delay, 3-day follow-up, 7-day email) | 2hr | Included in Twilio |
| Website form -> n8n webhook -> auto-response + ServiceM8 lead | 3hr | ~$1/mo |
| Steve notification via Telegram bot | 1hr | Free |
| Manual NZ directory submissions (Yellow, NoCowboys, Builderscrack, Finda) | 2hr | Free-$129/mo |
| Generate 10 suburb-targeted blog posts with Claude | 2hr | ~$2/mo |
| **Total** | **~13 hours** | **~$16-20/month** |

**Deliverables:**
- Every completed job triggers review request SMS
- Follow-up sequence for non-responders
- Website enquiries auto-triaged and auto-responded
- 10 local SEO blog posts published
- Listed on top 5 NZ directories

**Measurement:**
- Track: reviews/month (target: 8-12, up from ~3-5)
- Track: response time to enquiries (target: <5 min auto-response)
- Track: website traffic from local SEO pages

---

### Phase 3: Investment, Ongoing (~$25-40/month)

**Goal:** Video content machine + full SEO domination.

| Task | Time | Cost |
|------|------|------|
| ElevenLabs setup + voice cloning (Steve's voice) | 2hr | $5/mo |
| Video template design (Remotion or Creatomate) | 4hr | $0-12/mo |
| n8n workflow: tip -> script -> voiceover -> video -> upload (YT/IG/FB) | 4hr | Included |
| Stock footage library (20 plumbing clips from Pexels) | 2hr | Free |
| YouTube channel setup + Shorts optimization | 1hr | Free |
| Generate remaining 40 suburb blog posts | 3hr | ~$4 one-time |
| Monthly content calendar automation | 2hr | Free |
| **Total** | **~18 hours** | **~$25-40/month** |

**Deliverables:**
- Weekly AI-voiced plumbing tip video on YouTube Shorts + Instagram Reels
- 50+ suburb-targeted SEO pages
- Full content calendar running on autopilot

**Measurement:**
- Track: YouTube Shorts views, subscriber growth
- Track: Google ranking for suburb keywords (monthly audit)
- Track: inbound leads attributed to content

---

## Total Monthly Cost Summary

| Phase | Monthly Cost | Annual Cost | Key Metric |
|-------|-------------|-------------|------------|
| Phase 1 | ~$3 USD | ~$36 USD | Automated social presence |
| Phase 2 | ~$20 USD | ~$240 USD | +5-10 reviews/month |
| Phase 3 | ~$35 USD | ~$420 USD | Video content + SEO dominance |
| **All phases** | **~$35 USD (~$57 NZD)** | **~$420 USD (~$680 NZD)** | Full automation |

For context: a single plumbing job in Auckland averages $150-500 NZD. If this pipeline generates even ONE extra job per month, ROI is 3-9x.

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Meta API token expires | n8n error notification -> Steve re-authenticates (quarterly) |
| Claude generates inappropriate caption | Add moderation check node; Steve gets Telegram preview before posting (optional Phase 1 add-on) |
| SMS deliverability in NZ | Test with both Twilio and Sinch; use alphanumeric sender ID "StevePlumb" |
| Steve forgets to take photos | Weekly Telegram reminder; gamify with "streak counter" |
| Review request feels spammy | 2hr delay post-job, friendly tone, single follow-up only, easy opt-out |
| GBP API quota | Apply early; default is 0, approval takes 1-3 days |
| Video quality too low | Start with text-overlay videos (simpler), upgrade to stock footage + voiceover after testing |

---

## Quick-Win: The "Steve Workflow"

Steve's daily routine becomes:
1. Finish job
2. Take photo (muscle memory -- same as already showing customer the work)
3. Photo auto-uploads
4. Everything else is automated

That's it. One action (photo) triggers:
- Social media post (Facebook + Instagram + GBP)
- Review request SMS (2hr later)
- Job marked complete in ServiceM8
- Content logged for weekly/monthly roundups

---

## Technical Notes

### n8n Infrastructure
- Already running on Hetzner CAX11 (4GB RAM, ARM64)
- Current usage: ~846 MiB. Adding these workflows adds minimal load (~50-100MB)
- Access: SSH tunnel `ssh -L 5678:localhost:5678 root@178.104.85.59`
- **TODO from memory:** Still need Traefik reverse proxy for webhook URLs (required for ServiceM8 webhooks + website form)
- **TODO:** Set up Tailscale for easier access

### API Keys Needed
1. Claude API key (Anthropic) -- already have
2. Meta Developer App (Facebook/Instagram)
3. Google Cloud Console project (GBP API + YouTube Data API)
4. Twilio account + API key
5. ElevenLabs API key (Phase 3)
6. ServiceM8 API key

### Webhook Endpoint
ServiceM8 and website forms need a public webhook URL. Options:
- Traefik reverse proxy on Hetzner (recommended, free)
- ngrok (free tier, limited)
- Cloudflare Tunnel (free, excellent)

---

## Sources
- [n8n Google Business Profile integration](https://n8n.io/integrations/google-business-profile/)
- [n8n GBP posting workflow template](https://n8n.io/workflows/6165-automate-google-business-profile-posts-with-gpt-4-and-google-sheets/)
- [n8n Instagram + Google Drive + AI captions workflow](https://n8n.io/workflows/3478-automate-instagram-posts-with-google-drive-ai-captions-and-facebook-api/)
- [n8n ServiceM8 integration](https://n8n.io/integrations/servicem8/)
- [ServiceM8 n8n connection guide](https://support.servicem8.com/help-center/servicem8-add-ons/n8n/how-to-connect-servicem8-to-n8n)
- [n8n YouTube Shorts automation](https://n8n.io/workflows/2941-youtube-shorts-automation-tool/)
- [Creatomate + n8n YouTube Shorts guide](https://creatomate.com/blog/how-to-automatically-create-youtube-shorts-with-n8n)
- [Instagram automation without getting banned (2026)](https://dev.to/fermainpariz/how-to-automate-instagram-posts-in-2026-without-getting-banned-3nc0)
- [Twilio NZ SMS pricing](https://www.twilio.com/en-us/sms/pricing/nz)
- [Twilio NZ SMS guidelines](https://www.twilio.com/en-us/guidelines/nz/sms)
- [NZ SMS compliance guide](https://www.sent.dm/resources/new-zealand-sms-guide)
- [NZ business directories for trades (Tradify)](https://www.tradifyhq.com/blog/small-business-directories-for-nz-trade-businesses)
- [Top NZ citation sites (BrightLocal)](https://www.brightlocal.com/resources/top-citation-sites/location/new-zealand/)
- [ElevenLabs pricing](https://elevenlabs.io/pricing)
- [GBP automation guide 2026](https://almcorp.com/blog/automate-google-business-profile-management-complete-guide/)
