# Email Template: Request IDX Data Feed Access from Your Brokerage

---

## Email 1: Initial Request to Broker of Record

**To:** [Broker of Record Name]
**Subject:** Request for IDX/VOW Data Feed Access — Personal Agent Website

---

Hi [Broker Name],

I hope you're doing well. I'm reaching out because I'm building a personal real estate website to help generate leads and better serve my clients. The site will feature an interactive property search with map-based browsing — similar to what platforms like HouseSigma and Realtor.ca offer, but branded under our brokerage.

To make the property search functional, I need access to the **TRREB IDX (Internet Data Exchange)** data feed. As you know, IDX feed access is granted through the brokerage's TRREB membership.

**What I'm asking for:**

1. **Your authorization** for me to use the brokerage's IDX data feed on my personal agent website
2. **TRREB Technology team** to issue API/RETS credentials under the brokerage's IDX license

**What this involves on your end:**

- Contact TRREB Technology Services at **416-443-8100** or email **technology@trreb.ca**
- Request IDX data feed access (RESO Web API or RETS credentials)
- Sign the **TRREB IDX License Agreement** (if the brokerage doesn't already have one)

**What I'll handle:**

- All website development and hosting costs
- Compliance with TRREB's IDX display rules (proper disclaimers, data attribution, refresh intervals)
- The brokerage will be prominently displayed on every page per TRREB requirements

**Benefits for the brokerage:**

- Additional online presence and lead generation channel
- All leads coming through the site are attributed to our brokerage
- No cost to the brokerage — I'm covering all development and hosting
- Strengthens our digital footprint in the GTA market

I'd be happy to walk you through the site design and compliance plan whenever works for you. Would you have a few minutes this week to discuss?

Thank you,
[Your Name]
[Your Phone]
[Your RECO License Number]

---

## Email 2: Follow-up (if they say yes)

**To:** TRREB Technology Services
**CC:** [Broker of Record Name]
**Subject:** IDX Data Feed Application — [Brokerage Name]

---

Hello,

I am writing on behalf of **[Brokerage Name]** (TRREB Member #[Member Number]) to request IDX data feed access for a brokerage-authorized agent website.

**Brokerage Details:**
- Brokerage Name: [Brokerage Legal Name]
- TRREB Member Number: [Number]
- Broker of Record: [Name]
- Broker Contact Email: [Email]

**Technical Details:**
- Intended use: Personal agent website with IDX property search
- Preferred feed format: **RESO Web API** (preferred) or RETS
- Website URL: [Your planned domain]
- Developer contact: [Your Name / Email]

**We request:**
1. RESO Web API or RETS login credentials
2. Documentation for field mappings and photo access
3. IDX compliance checklist

Our Broker of Record ([Name]) has authorized this request and is CC'd on this email for confirmation.

Please let us know what additional documentation or agreements are required to proceed.

Thank you,
[Your Name]
[Phone]

---

## Key Things to Know

### TRREB IDX Rules You Must Follow
Once you get access, your website must comply with these display rules:

1. **Brokerage identification** — Your brokerage name and phone number must be clearly displayed on every page showing IDX data
2. **Listing attribution** — Each listing must show the listing brokerage name
3. **Data freshness** — IDX data must be refreshed at least every **4 hours** (recommended: every 15 min)
4. **Disclaimer** — Must display: *"The listing data is provided under copyright by the Toronto Regional Real Estate Board. The listing data is deemed reliable but is not guaranteed accurate by TRREB."*
5. **No scraping** — Data cannot be scraped, copied, or redistributed
6. **Registration optional** — You CAN require users to register (VOW) but it's not mandatory for IDX
7. **Sold data** — Only available through **VOW** (Virtual Office Website), which requires user registration/login. This is why we built the auth system.

### IDX vs VOW — What to Request

| Feature | IDX | VOW |
|---------|-----|-----|
| Active listings | Yes | Yes |
| Sold prices | **No** | **Yes** (logged-in users only) |
| User registration required | No | Yes |
| Days on Market | Limited | Full |
| Listing history | No | Yes |
| Requires auth system | No | Yes — user must acknowledge terms |

**Recommendation:** Request **both IDX and VOW** access. Our platform already has user authentication built in, so we can serve IDX data publicly and VOW data (sold prices) to logged-in users — exactly like HouseSigma does it.

### Timeline Expectations
- Broker agrees and contacts TRREB: **1-3 days**
- TRREB processes IDX application: **1-2 weeks**
- IDX agreement signed: **1-3 days**
- Credentials issued: **1-3 days**
- **Total: 2-4 weeks**

### If Your Broker Asks Questions

**"Will this cost me anything?"**
No. You're covering all development and hosting. The IDX feed is included with the brokerage's existing TRREB membership.

**"What about compliance?"**
You'll handle all TRREB compliance requirements. Happy to show them the compliance plan.

**"Who owns the leads?"**
All leads come through the brokerage. Every page shows the brokerage name and contact info per TRREB rules.

**"Can I see the website first?"**
Absolutely — you can demo the platform. It won't have live data until the feed is connected, but the UI and functionality are fully built.
