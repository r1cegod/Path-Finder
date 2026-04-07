# Retrieval Research Sources

Reference for domain selection in the web-enabled stages: `job`, `major`, `uni`.

## 1. Domain Priority

Use this order of trust:

1. Official source for the exact institution or authority
2. Vietnam-specific primary market source
3. Reputable secondary reporting
4. Forum / Reddit discussion only as supplementary reality-check context

## 2. Recommended Domains

### Job

Use for salary, hiring reality, role descriptions, and market demand:

- `itviec.com`
- `topcv.vn`
- `vietnamworks.com`
- `careerviet.vn`
- `glints.com`
- `jobstreet.vn`

Use official company career pages when the student names a specific company or company type.

### Major

Use for curriculum reality, necessity squeeze, and industry bridge checks:

- `moet.gov.vn`
- official university domains ending in `.edu.vn`
- `topcv.vn`
- `glints.com`
- `thanhnien.vn`
- `tuoitre.vn`

Rule:
- Prefer official school curriculum pages over generic “ngành X là gì” articles.

### University

Use for admissions, tuition, and official program structures:

- `moet.gov.vn`
- official university domains ending in `.edu.vn`
- `vnu.edu.vn`
- `vnuhcm.edu.vn`
- `hust.edu.vn`
- `hcmut.edu.vn`
- `ftu.edu.vn`
- `neu.edu.vn`
- `thanhnien.vn`
- `tuoitre.vn`
- `dantri.com.vn`

Rule:
- For admissions, tuition, and curriculum, official school pages beat media summaries.

## 3. Query Style

Bad:
- one giant “research request” query mixing salary, remote, meetings, autonomy, and company stage

Good:
- one narrow query per contradiction
- salary query
- day-to-day / stakeholder-load query
- admissions / tuition / curriculum query

Examples:

- `site:itviec.com OR site:topcv.vn Data Scientist Việt Nam lương`
- `site:reddit.com Product Manager stakeholder meetings day to day`
- `site:hcmut.edu.vn khoa chương trình đào tạo khoa học máy tính tín chỉ`

## 4. Reddit

### What is currently available

1. **Official Reddit Data API**
   - Best option for structured fetches.
   - Requires OAuth, a registered app/client, and a descriptive User-Agent.
   - Reddit's current Data API wiki says traffic not using OAuth or login credentials will be blocked.

2. **Search-engine discovery**
   - Works today with Serper using `site:reddit.com` or `site:old.reddit.com`.
   - Good for finding relevant threads.
   - Weak for reliable extraction because snippets are noisy and incomplete.

3. **Legacy `.json` endpoints**
   - Still referenced in legacy technical guidance.
   - Treat as unstable / non-primary because Reddit's current Data API wiki explicitly says some legacy API documentation is out of date.

### Recommendation for PathFinder

- Short term:
  - Use Serper only for Reddit discovery.
  - Do not treat Reddit snippets as hard evidence.

- Medium term:
  - If Reddit becomes important for reality-check evidence, add a dedicated Reddit fetcher using the official Data API.
  - Keep Reddit as a supplementary source, not the primary source for salary, tuition, admissions, or official curriculum facts.
