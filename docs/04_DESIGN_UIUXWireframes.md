# DESIGN DOCUMENTS
## Creator OS - UI/UX Wireframes, User Flows & Interactive Prototypes

**Document Version:** 1.0  
**Last Updated:** September 2026  
**Owner:** UI/UX Design Team  
**Status:** Framework with High-Fidelity Specifications

---

## 1. DESIGN PHILOSOPHY & PRINCIPLES

### Core Design Principles

**1. Clarity Over Complexity**
- Every screen has one primary action
- Minimize cognitive load (users are creators, not engineers)
- Clear hierarchy: What should I do first?

**2. Trust Through Transparency**
- Show why the system flagged something (claim dedup, authenticity score, etc.)
- Explain confidence levels (high/medium/low)
- Trace every claim back to source
- Let creator override system recommendations

**3. Respect Creator's Time**
- Minimize interaction steps (approve/reject should be 1-click)
- Show only necessary information (hide QA details unless needed)
- Batch operations where possible (review all 4 channels at once)

**4. Feedback-Forward Design**
- Creator feedback instantly visible ("3/5 outputs approved this week")
- Learning visible ("System improved 8% based on your feedback")
- Celebrate progress ("You published 3x more content this month")

**5. Non-Homogenizing**
- Highlight when output might lack creator's voice
- Show authenticity score prominently
- Flag similar claims before creator publishes

---

## 2. USER JOURNEYS & FLOWS

### Journey 1: First-Time Setup (Week 1)

```
Creator Lands on CreatorOS
       ↓
  Login / Signup
       ↓
  "Let's Set Up Your Archive"
       ↓
  Upload 20+ Published Pieces
       ↓
  System Indexes & Generates Voice Profile
       ↓
  Creator Reviews Profile ("Does this sound like me?")
       ↓
  Approve or Request Adjustments
       ↓
  Setup Complete → Ready for First Content
```

**Duration:** 15-20 minutes  
**Key Moments:** 
- Creator sees their voice profile visualized (builds confidence)
- System shows claim extraction (builds trust in dedup)

---

### Journey 2: Content Transformation (Typical Workflow)

```
Creator Has New Content (transcript, notes, etc.)
       ↓
  Upload Raw Material
       ↓
  "Processing..." (45-60 seconds)
       ↓
  Dashboard: 4 Channel Outputs Ready
       ↓
  Creator Reviews Each Output
       ├─ Read content
       ├─ Check authenticity score
       ├─ Check for flagged claims/redundancy
       └─ Approve or Reject
       ↓
  Creator Approves Output
       ↓
  Export & Publish
       (LinkedIn / Newsletter / Twitter / Blog)
```

**Duration:** 10-15 minutes per source  
**Critical UX Points:**
- All 4 outputs visible at once (side-by-side)
- Approval/rejection one click
- QA details expandable (don't clutter default view)

---

### Journey 3: Learning Loop (Feedback Cycle)

```
Creator Rejects Output
       ↓
  "Why?" (optional feedback)
       ├─ Voice is off
       ├─ Already said this
       ├─ Misses the point
       └─ Other [comment]
       ↓
  System Captures Feedback
       ↓
  Every 10 Runs: "Here's what I learned"
       ├─ Approval rate: 68% (↑ from 54% week 1)
       ├─ False claim flags: ↓ 3 (improved accuracy)
       └─ Your style: More "tactical frameworks"
       ↓
  Creator Sees Improvement in Next Outputs
```

**Duration:** Ongoing (async)  
**Key Moments:**
- Rejection feedback feels lightweight (not burdensome)
- Learning visible and celebratory ("You helped me learn X")

---

## 3. INFORMATION ARCHITECTURE

### Navigation Structure

```
CreatorOS Dashboard
├── Home / Overview
│   ├── Quick Stats (approval rate, outputs this week)
│   ├── Recent Outputs (last 5)
│   └── Getting Started Tip
│
├── Upload & Process
│   ├── New Source Material (upload form)
│   ├── Processing Queue (status of in-progress)
│   └── Historical Sources (past 20)
│
├── Review Dashboard
│   ├── Pending Approval (newest first)
│   ├── Approved Outputs
│   ├── Rejected Outputs
│   └── Archive Search
│
├── Learning & Insights
│   ├── Approval Trends (chart over time)
│   ├── Rejection Patterns (channel, content type)
│   ├── System Improvements (weekly)
│   └── Archive Stats (voice profile, claim index)
│
├── Settings
│   ├── Archive Management (upload, delete, refresh)
│   ├── Preferences (channels, tone, scheduling)
│   ├── Integrations (LinkedIn, Twitter API)
│   ├── Privacy (data usage, exports)
│   └── Profile (name, email, preferences)
│
└── Help & Support
    ├── FAQ
    ├── Getting Started
    ├── Video Tutorials
    └── Contact Support
```

---

## 4. SCREEN DESIGNS & WIREFRAMES

### Screen 1: Dashboard Home

**Purpose:** At-a-glance overview of system health and creator's progress

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Creator OS                     [Settings] [Help]│
├─────────────────────────────────────────────────┤
│                                                   │
│  Welcome back, [Creator Name]!                   │
│                                                   │
│  📊 THIS WEEK'S METRICS                          │
│  ┌──────────────────────────────────────────┐   │
│  │ Approval Rate:  68% ↑ +8% from last week │   │
│  │ Outputs Created: 12                      │   │
│  │ Published: 8                             │   │
│  │ Time Saved: ~6 hours                     │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  🎯 PENDING REVIEW                              │
│  ┌──────────────────────────────────────────┐   │
│  │ 3 outputs waiting for approval           │   │
│  │ [View Pending] →                         │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  📈 RECENT UPLOADS                              │
│  ┌──────────────────────────────────────────┐   │
│  │ [Thu 12:45] Podcast Ep. 47 Transcript    │   │
│  │             4 outputs ready              │   │
│  │             [Review Now] →               │   │
│  │                                          │   │
│  │ [Wed 14:20] LinkedIn Post Notes          │   │
│  │             All approved & published     │   │
│  │                                          │   │
│  │ [Tue 10:30] Newsletter Outline           │   │
│  │             Awaiting approval            │   │
│  │             [Review] →                   │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  💡 TIP: Your voice profile was updated based    │
│  on your feedback. Your "short sentences"        │
│  preference is now reflected in outputs.         │
│                                                   │
└─────────────────────────────────────────────────┘
```

**Key Interactions:**
- Click metric to drill down (approval rate → breakdown by channel)
- "View Pending" → Navigates to Review Dashboard
- "Review Now" → Opens specific source's outputs for review

---

### Screen 2: Upload & Processing

**Purpose:** Creator submits raw content and monitors progress

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Creator OS > Upload New Content                │
├─────────────────────────────────────────────────┤
│                                                   │
│  📤 UPLOAD YOUR CONTENT                          │
│                                                   │
│  What do you have?                              │
│  ( ) Audio recording (.mp3, .wav)              │
│  ( ) Transcript (.txt, .md)                     │
│  ( ) Notes / Outline (.md, .txt)               │
│  ( ) Link to published content                  │
│                                                   │
│  ┌─────────────────────────────────────────┐   │
│  │                                           │   │
│  │  Drag files here or click to browse      │   │
│  │  Max 1GB, .mp3/.wav/.txt/.md/.docx      │   │
│  │                                           │   │
│  │           [Choose File]                   │   │
│  │                                           │   │
│  └─────────────────────────────────────────┘   │
│                                                   │
│  📝 Add a Title (optional)                      │
│  [Podcast Ep. 47 - AI for Creators]            │
│                                                   │
│  ⏱️  Source Duration: 40 minutes                │
│                                                   │
│  📍 Mark Key Sections (optional)                │
│  "This part is really important"               │
│  [+ Add Section Highlight]                     │
│                                                   │
│                        [Cancel]  [Next → ]     │
│                                                   │
├─────────────────────────────────────────────────┤
│                                                   │
│  🔄 PROCESSING QUEUE                            │
│  ┌─────────────────────────────────────────┐   │
│  │ Podcast Ep. 47 Transcript               │   │
│  │ ████████░░ 80% complete                 │   │
│  │ Est. 1 min remaining                    │   │
│  │ [View Output] (when ready)              │   │
│  │                                          │   │
│  │ LinkedIn Article Notes                  │   │
│  │ ✓ Processing complete!                  │   │
│  │ 4 outputs ready → [Review Now]          │   │
│  └─────────────────────────────────────────┘   │
│                                                   │
└─────────────────────────────────────────────────┘
```

**Key Interactions:**
- File upload with progress indicator
- Optional source metadata (title, duration)
- Processing queue shows status in real-time
- "View Output" navigates to review screen when ready

---

### Screen 3: Review Dashboard (Core UX)

**Purpose:** Creator reviews 4 channel outputs side-by-side, makes approval decisions

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Creator OS > Review Outputs                    │
│  SOURCE: Podcast Ep. 47 Transcript (12:45 PM)  │
├─────────────────────────────────────────────────┤
│                                                   │
│  📍 4 OUTPUTS READY FOR REVIEW                   │
│                                                   │
│  Channel View:  [All] [Thread] [Newsletter]     │
│                 [Carousel] [Blog]               │
│                                                   │
│  ┌──────────────┬──────────────┬──────────────┐ │
│  │   THREAD     │ NEWSLETTER   │   CAROUSEL   │ │
│  ├──────────────┼──────────────┼──────────────┤ │
│  │              │              │              │ │
│  │ Thread text: │ Email-ready  │ 3 slides:   │ │
│  │ [8-12 tweets]│ HTML + plain │ "Teaser"    │ │
│  │              │ text format  │ + 2 body    │ │
│  │ Tweet 1:     │              │              │ │
│  │ "Just wrapped│ Hi [Name],   │ Slide 1:    │ │
│  │  a 40-min    │              │ [Visual]     │ │
│  │  convo on AI │ I wanted to  │ "Key Point"  │ │
│  │  for         │ share 3 key  │              │ │
│  │  creators..."│ insights...  │ Slide 2:     │ │
│  │              │              │ [Body 1]     │ │
│  │ Tweet 2:     │ [Full text]  │              │ │
│  │ "Why many    │              │ Slide 3:     │ │
│  │  creators    │ Looking      │ [Body 2]     │ │
│  │  fail with   │ forward to   │              │ │
│  │  AI:..."     │ your        │ [Footer CTA]│ │
│  │              │ thoughts!    │              │ │
│  │ [+ 6 more]   │              │              │ │
│  │              │              │              │ │
│  └──────────────┴──────────────┴──────────────┘ │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │  QUALITY CHECK: THREAD                   │   │
│  ├──────────────────────────────────────────┤   │
│  │                                          │   │
│  │  ✅ Authenticity Score: 84%              │   │
│  │     "Sounds like you - High confidence"  │   │
│  │                                          │   │
│  │  ⚠️  Claim Alert:                        │   │
│  │     "I interviewed 200+ creators" also  │   │
│  │     appears in your July 20 post        │   │
│  │     Similarity: 92% | [View Original]   │   │
│  │                                          │   │
│  │  ✅ Redundancy: Clear (unique angle)    │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  YOUR DECISION:                                  │
│  [👍 APPROVE] [👎 REJECT]                       │
│                                                   │
│  If rejecting, tell us why (optional):         │
│  ( ) Voice is off                               │
│  ( ) Already said this                          │
│  ( ) Misses the point                           │
│  ( ) Other [comment field...]                   │
│                                                   │
│  ─────────────────────────────────────────────  │
│  [Reject] [Next Output ↓]                      │
│                                                   │
└─────────────────────────────────────────────────┘

[Similar layout for Newsletter, Carousel, Blog with scrollable content]
```

**Key Interactions:**
- **Tab between channels** (Thread, Newsletter, Carousel, Blog)
- **Click "View Original"** → Show source claim in archive
- **Approve/Reject buttons** → One-click decision
- **Optional feedback** → Creator explains rejection (helps system learn)
- **Quality Check expansion** → Show/hide QA details as needed

**Mobile Adaptation:**
- Stack channels vertically (swipe between them)
- Approve/Reject buttons large and thumb-friendly
- QA details collapsed by default

---

### Screen 4: Learning & Insights Dashboard

**Purpose:** Show creator how system is improving over time

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Creator OS > Learning & Insights               │
├─────────────────────────────────────────────────┤
│                                                   │
│  📚 SYSTEM LEARNING                              │
│                                                   │
│  After 50+ outputs, here's what I learned:     │
│                                                   │
│  ✅ You Prefer:                                 │
│  • Short sentences (avg 12 words, not 18)      │
│  • Tactical frameworks (step-by-step > theory) │
│  • Stories + data (you combine narrative +     │
│    stats)                                       │
│  • Punchy headlines (2-3 words, not long)      │
│                                                   │
│  📈 APPROVAL TRENDS                             │
│  ┌──────────────────────────────────────────┐   │
│  │                                          │   │
│  │  Approval Rate by Channel:               │   │
│  │                                          │   │
│  │  Thread    ████████░░ 72% ↑ +12%        │   │
│  │  Newsletter ██████░░░░ 55% ↓ -5%        │   │
│  │  Carousel  █████████░ 78% ↑ +3%         │   │
│  │  Blog      ████░░░░░░ 42% ↓ -8%         │   │
│  │                                          │   │
│  │  Overall:  ████████░░ 68%  ↑ +8%        │   │
│  │            (Week 1 → Now)                │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  🎯 REJECTION REASONS                           │
│  ┌──────────────────────────────────────────┐   │
│  │ Voice is off ████░░░░░░ 8 times         │   │
│  │ Already said ██░░░░░░░░ 2 times         │   │
│  │ Misses point ███░░░░░░░ 3 times         │   │
│  │ Other       ░░░░░░░░░░ 0 times         │   │
│  │                                          │   │
│  │ Note: Most rejections in "Newsletter"   │   │
│  │ channel - we're working on this!        │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  ✨ THIS WEEK'S IMPROVEMENTS                    │
│  ┌──────────────────────────────────────────┐   │
│  │ • Reduced claim false-positives by 40%   │   │
│  │   (you said "over-flagging" → we listened)│  │
│  │ • Improved newsletter voice by 15%       │   │
│  │ • Caught 2 real redundancies before pub  │   │
│  │ • You saved ~4 hours this week!          │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  🗣️  YOUR VOICE FINGERPRINT                    │
│  ┌──────────────────────────────────────────┐   │
│  │ Characteristic    Your Style  Industry    │   │
│  │ Avg Sentence      12 words   (avg: 14)   │   │
│  │ Vocabulary        Accessible (not jargony)│  │
│  │ Argument Style    Tactical   (how-to)    │   │
│  │ Unique Traits     • Uses data + story    │   │
│  │                   • Provocative headlines│   │
│  │                   • Personal examples    │   │
│  │                                          │   │
│  │ [Refresh Profile] (if feeling different) │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
└─────────────────────────────────────────────────┘
```

**Key Interactions:**
- Click on approval trend → drill down by week/channel/content type
- Hover on reason → see examples of that rejection type
- "Refresh Profile" → Re-analyze archive for voice changes
- All charts/numbers link to deeper analytics (if needed)

---

### Screen 5: Archive Management

**Purpose:** Creator manages their published content (the reference standard)

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Creator OS > Archive Settings                  │
├─────────────────────────────────────────────────┤
│                                                   │
│  📚 YOUR PUBLISHED ARCHIVE                       │
│                                                   │
│  The foundation of your voice profile           │
│  Currently: 47 published pieces                 │
│  Last updated: 2 hours ago                      │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │                                          │   │
│  │  📊 Archive Stats:                       │   │
│  │  ├─ Total Pieces: 47                     │   │
│  │  ├─ Channels: LinkedIn, Newsletter, Blog │   │
│  │  ├─ Date Range: Mar 2023 - Now           │   │
│  │  ├─ Avg. Engagement: ⭐ 2.3k likes      │   │
│  │  └─ Claims Extracted: 185               │   │
│  │                                          │   │
│  │  Your Voice Profile Confidence:          │   │
│  │  ████████░░ 92% (very confident!)       │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  🔄 ADD / UPDATE ARCHIVE                        │
│                                                   │
│  [+ Upload New Pieces]                          │
│  Bulk upload or paste URLs                      │
│                                                   │
│  📋 Archive Contents:                           │
│                                                   │
│  [Search: _________] [Filter: All] [View: List]│
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │ Piece | Channel  | Date       | Status   │   │
│  ├──────────────────────────────────────────┤   │
│  │ "Why AI Fails..."    │ LinkedIn │ Apr 15 │✅ │   │
│  │ Newsletter #42       │ Email    │ Apr 10 │✅ │   │
│  │ "Authenticity Beats" │ Blog     │ Apr 5  │✅ │   │
│  │ "3 Creator Trends"   │ LinkedIn │ Mar 28 │✅ │   │
│  │ ...                  │ ...      │ ...    │   │   │
│  │                                          │   │
│  │ [Load more...]                           │   │
│  │                                          │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  ⚙️ ARCHIVE ACTIONS                             │
│                                                   │
│  [Refresh Voice Profile] (re-analyze archive)  │
│  [Check Archive Health] (look for issues)      │
│  [Backup Archive] (download all pieces)        │
│  [Edit Archive] (remove/update pieces)         │
│                                                   │
│  ℹ️  Why archive matters:                       │
│  • We use it to check if outputs match your    │
│    voice                                        │
│  • We use it to find claims you've made        │
│    before (prevent repetition)                  │
│  • It stays completely private and secure      │
│                                                   │
└─────────────────────────────────────────────────┘
```

**Key Interactions:**
- Upload new pieces → Automatically re-index and update voice profile
- Click piece → View in archive, see all claims extracted
- Refresh Profile → Trigger re-analysis (useful if creator feels they've evolved)
- Backup Archive → Download all pieces as .zip

---

## 5. CRITICAL INTERACTION PATTERNS

### Pattern 1: Approval/Rejection with Feedback

**User Story:** Creator reviews output and rejects with feedback

**Flow:**
```
User sees output
       ↓
User clicks [Reject] button
       ↓
Modal/form appears with rejection reasons:
├─ Voice is off
├─ Already said this
├─ Misses the point
└─ Other [text field]
       ↓
User selects reason (optional comment)
       ↓
User clicks [Confirm Rejection]
       ↓
System: "Got it. Feedback recorded."
Next output auto-displays (or shows "No more outputs")
       ↓
System: Learn loop triggered (if 10+ feedback points)
```

**Design Decisions:**
- Rejection should NOT feel punitive (system learns from it)
- Feedback optional but encouraged
- Immediate confirmation that feedback was recorded

---

### Pattern 2: QA Details (Claim Flag Example)

**User Story:** Creator sees claim flagged for redundancy, wants to understand

**Flow:**
```
User sees:
┌──────────────────────────────┐
│ ⚠️ Claim Alert:              │
│ "I interviewed 200+ creators"│
│ appears in your July 20 post │
│ Similarity: 92%              │
│ [View Original ↗]            │
└──────────────────────────────┘
       ↓
User clicks [View Original]
       ↓
Modal/sidebar opens showing:
┌──────────────────────────────┐
│ ORIGINAL (July 20, 2024)     │
│ LinkedIn Post                │
│ "...I interviewed 200+       │
│ creators for this report..."  │
└──────────────────────────────┘
       ↓
User sees context, decides:
- "I can reword it" → Reject output, reword manually
- "It's OK to repeat" → Override flag, approve anyway
- "System is wrong" → Mark as false positive
```

**Design Decisions:**
- Links are discoverable but not forced
- Creator can override system (trust, not autocracy)
- False positive feedback helps learning

---

### Pattern 3: Learning Feedback (Weekly)

**User Story:** Creator sees weekly learning summary

**Display:**
```
Notification / Dashboard Widget:
┌───────────────────────────────┐
│ 🎯 SYSTEM LEARNING SUMMARY   │
│                               │
│ Based on your feedback:       │
│                               │
│ ✅ Improved newsletter voice  │
│    (approval +12% this week)  │
│                               │
│ ✅ Reduced false claim flags  │
│    (you were right 8/10 times)│
│                               │
│ ℹ️  Added: "Prefer shorter    │
│    paragraphs" to your style  │
│                               │
│ [See Details →]              │
└───────────────────────────────┘
```

---

## 6. ACCESSIBILITY REQUIREMENTS

### WCAG 2.1 AA Compliance

**Color Contrast:**
- All text ≥ 4.5:1 ratio (normal text)
- ≥ 3:1 for large text (18pt+)
- Never rely on color alone (use icons + text for flags)

**Keyboard Navigation:**
- All interactive elements accessible via Tab
- Focus visible (outline or highlight)
- Escape key closes modals
- Enter key submits forms

**Screen Reader Support:**
- All images have alt text
- Form labels associated with inputs
- Headings in proper order (H1 → H2 → H3)
- ARIA labels for icons-only buttons (e.g., "Approve output")

**Motion & Animation:**
- Prefers-reduced-motion respected
- No auto-play videos or auto-scrolling
- Animations ≤ 5 seconds

**Mobile Accessibility:**
- Touch targets ≥ 44x44px
- Text resizable up to 200%
- No horizontal scrolling (except tables)

---

## 7. RESPONSIVE DESIGN STRATEGY

### Breakpoints
- **Mobile:** 375px - 599px (default design)
- **Tablet:** 600px - 1023px (optimized layout)
- **Desktop:** 1024px+ (full experience)

### Mobile Adaptations

**Dashboard Home:**
- Metrics cards stack vertically
- "Pending Review" badge in header (tap to jump)
- Recent uploads as carousel (swipe)

**Review Dashboard:**
- Channels as vertical tabs (swipe between)
- Output content scrollable
- Approve/Reject buttons stick to bottom (always visible)

**Archive Management:**
- List view optimized for mobile (one column)
- Piece details in modal (not drawer)
- Upload button always visible (floating action button)

---

## 8. DARK MODE & THEMING

**Color Palette:**

**Light Mode:**
- Background: #FFFFFF
- Surfaces: #F5F7FA
- Text Primary: #1A1A1A
- Text Secondary: #666666
- Accent (Approve): #2ECC71 (green)
- Accent (Reject): #E74C3C (red)
- Alert (Claim Flag): #F39C12 (orange)
- Neutral (Success): #3498DB (blue)

**Dark Mode:** (inverted + adjusted)
- Background: #0A0A0A
- Surfaces: #1A1A1A
- Text Primary: #FFFFFF
- Text Secondary: #CCCCCC
- Accent colors brightened

**System Font Stack:**
```
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

---

## 9. ERROR STATES & EDGE CASES

### Error 1: Upload Failed
```
┌──────────────────────────────┐
│ ❌ Upload Failed             │
│                              │
│ File too large (>1GB)        │
│ Max file size: 1 GB          │
│ Your file: 1.2 GB           │
│                              │
│ [Try Again] [Contact Support]│
└──────────────────────────────┘
```

### Error 2: Transcription Failed
```
┌──────────────────────────────┐
│ ⚠️  Transcription Issue      │
│                              │
│ Audio was too quiet or       │
│ unclear (confidence: 34%)    │
│                              │
│ Option A: Upload transcript  │
│          manually (.txt)     │
│                              │
│ Option B: Try different file │
│                              │
│ [Upload] [Cancel]           │
└──────────────────────────────┘
```

### Edge Case: No Outputs Generated
```
┌──────────────────────────────┐
│ ⚠️  Hmm, No Outputs Yet      │
│                              │
│ The system couldn't generate │
│ outputs from this content.   │
│                              │
│ Possible reasons:            │
│ • Content too short (<100 w) │
│ • No clear claims to extract │
│ • Topic outside your archive │
│                              │
│ What to try:                 │
│ 1. Upload longer source      │
│ 2. Combine with another note │
│ 3. Contact support           │
│                              │
│ [Upload Different] [Support] │
└──────────────────────────────┘
```

---

## 10. ONBOARDING & EMPTY STATES

### First-Time User (Empty Archive)

```
┌────────────────────────────────────┐
│  Welcome to Creator OS! 🎉         │
├────────────────────────────────────┤
│                                    │
│  Let's get you set up in 3 steps:  │
│                                    │
│  1️⃣  Upload Your Archive           │
│      20+ of your published pieces  │
│      ✅ This builds your voice     │
│         fingerprint              │
│                                    │
│      [Upload Archive →]           │
│                                    │
│  2️⃣  Upload Raw Content           │
│      Transcript, audio, notes, etc.│
│                                    │
│  3️⃣  Review & Approve             │
│      Tell us what you like/dislike │
│                                    │
│  ─────────────────────────────────  │
│  Let's start with your archive    │
│  (takes 10-15 minutes)            │
│                                    │
│  [Get Started]                     │
│                                    │
└────────────────────────────────────┘
```

### First Content Uploaded (Generating)

```
┌────────────────────────────────────┐
│  Processing Your Content... ✨     │
├────────────────────────────────────┤
│                                    │
│  Step 1: Transcribe Audio         │
│  ████████░░ 75% (30 sec)           │
│                                    │
│  Step 2: Generate Outputs         │
│  ░░░░░░░░░░ (starting...)         │
│                                    │
│  Total time: ~60 seconds          │
│                                    │
│  While you wait:                  │
│  • Your voice profile is 92%      │
│    confident                      │
│  • We're analyzing archive        │
│  • Preparing 4 channel outputs    │
│                                    │
│  💡 Tip: Get a coffee!            │
│                                    │
└────────────────────────────────────┘
```

---

## 11. MICRO-INTERACTIONS & FEEDBACK

### Hover States
- Buttons: Slight color shift + cursor pointer
- Cards: Subtle shadow lift (elevation)
- Links: Underline appears

### Click States
- Button: Press-down effect (1px shift)
- Immediate visual feedback (0-100ms)
- Ripple or fade animation (optional, respectful)

### Loading States
- Skeleton screens for content (not spinners)
- Progress bars for long operations (>2 sec)
- Percentage shown if >30 sec operation

### Success States
- Brief confirmation message (2-3 sec toast)
- Green checkmark + "Saved" text
- Confetti optional (if creator's first approval!)

---

## 12. DESIGN COMPONENT LIBRARY

Components to build/reuse:

```
Layout Components:
├─ Header (with logo, creator name, settings menu)
├─ Sidebar Navigation
├─ Card (reusable container)
├─ Modal / Drawer
├─ Tab Component

Input Components:
├─ Text Input (with label, error state)
├─ File Upload (drag + drop)
├─ Radio Group (rejection reason)
├─ Button (primary, secondary, danger)
├─ Toggle Switch (channel filters)

Data Display:
├─ Table (archive list)
├─ Chart (approval trends)
├─ Metric Card (stats)
├─ Timeline (processing steps)

Feedback:
├─ Toast (brief notifications)
├─ Alert Box (warnings, errors)
├─ Skeleton Screen (loading)
├─ Tooltip (help info)
```

---

## APPENDIX: Figma & Prototype Notes

This document provides the **wireframes and interaction logic**. To build **high-fidelity prototypes**, create a Figma project with:

1. **Frame Structure:**
   - Page per screen (Dashboard, Upload, Review, etc.)
   - Components library (button, card, metric card, etc.)
   - Variants for states (hover, active, disabled, error)

2. **Interactive Prototypes:**
   - Link screens with triggers (button click → next screen)
   - Prototype approval flow
   - Prototype modal opening/closing
   - Prototype tab switching

3. **Design Handoff:**
   - Spacing specs (padding, margins in 8px grid)
   - Typography specs (font, size, weight, line height)
   - Color specs (hex values, usage guidelines)
   - Interaction specs (animations, transitions)
   - Export all screens as SVG for documentation

4. **Accessibility Audit:**
   - Run WAVE tool on prototype
   - Check color contrast (use WebAIM)
   - Test keyboard navigation (Tab through all screens)
   - Test with screen reader (NVDA or JAWS)

---

**Next Steps:**
1. Import wireframes into Figma
2. Create component library
3. Build interactive prototype (link screens)
4. User test with real creator (week 4 of development)
5. Iterate based on feedback
6. Handoff to engineering with detailed specs
