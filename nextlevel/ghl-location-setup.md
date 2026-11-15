# Create the "Next Level" sub-account in HighLevel

**Status, 2026-11-15:** Step 1 on the done checklist (create the sub-account) is verified. The sub-account is named "Next Level", location ID n0qwGpNQ3CShe8AIhyI0, seen in HighLevel's notices to Ray's inbox on 2026-11-15. Skip Part A steps 3 to 9, open it, and check its details in Part B. The remaining steps still apply.

**Check before any send:** a contact import ran into this sub-account on 2026-11-15 (HighLevel reported 88% deliverable, 10% high risk). Ray to say which list it was. Ray Homes consumer contacts must not be emailed about Next Level.

For Ray or Diana. Work top to bottom. Allow about one sitting, plus waiting time for domain and registration approvals.

HighLevel changes its menu names often. Where a name may differ on your screen it is marked `[verify menu name]`. The step still applies. Look for the closest match.

This creates a new sub-account. It does not change the Ray Homes sub-account. Do not edit, pause or delete anything in Ray Homes while doing this.

## Before you start

Have these ready:

- [ ] Agency owner or admin login.
- [ ] Legal business name and mailing address for Next Level. [Ray to confirm: business name and mailing address for Next Level]
- [ ] A domain for Next Level email and pages. [Ray to set: domain for Next Level]
- [ ] Access to that domain's DNS settings.
- [ ] The Next Level logo file.
- [ ] Email addresses for Ray, Diana and Nadiya.
- [ ] Stripe login. Note: Stripe verification is not done yet. Part E cannot be finished until it is.

## Part A. Create the sub-account

1. Log in to HighLevel.
2. Switch to the agency view. Top left, click the account switcher and choose "Switch to Agency View". [verify menu name]
3. In the left menu click "Sub-Accounts". [verify menu name]
4. Click "Create Sub-Account" (top right). [verify menu name]
5. When asked to choose a snapshot, choose the blank or default option for now. The Next Level sales snapshot is loaded in Part G. [verify menu name]
6. When asked how to add the business, choose to enter the details by hand rather than searching the map. [verify menu name]
7. Enter:
   - Business name: Next Level
   - Address: [Ray to confirm: business name and mailing address for Next Level]
   - Phone: Ray's business line for now
   - Email: the Next Level support email [Ray to set: support email for Next Level]
   - Time zone: Eastern (Toronto)
   - Country: Canada
8. If a SaaS plan field appears, leave it empty. This is our own account, not a paying client. [verify menu name]
9. Click "Save". [verify menu name]
10. Find Next Level in the sub-account list and click to open it. You are now inside the sub-account.

## Part B. Business profile

11. In the sub-account, click "Settings" (bottom left).
12. Click "Business Profile". [verify menu name]
13. Upload the Next Level logo.
14. Check the name, address, phone, email and time zone. Fix anything wrong.
15. Find the Location ID on this page and check it reads n0qwGpNQ3CShe8AIhyI0. If it differs, tell Ray. [verify menu name]
16. Click "Update" or "Save" in each section you changed. [verify menu name]

## Part C. Phone number

17. In Settings, click "Phone Numbers". [verify menu name]
18. Click "Add Number". [verify menu name]
19. Choose Canada. Search for a GTA area code Ray prefers. [Ray to set: area code for the Next Level number]
20. Pick a local number that can do voice and text. Buying a number costs money. Get Ray's yes before clicking buy.
21. Name the number "Next Level main".
22. Set where calls forward for now: Ray's phone. The demo voice agent is attached later.
23. Open "Trust Center" or the messaging registration page. [verify menu name] Read what must be filed before texts can send from this number. Start the registration with the legal business details. Approval can take days.
24. Do not send any text from this number until registration shows approved.

## Part D. Sending domain for email

25. In Settings, click "Email Services". [verify menu name]
26. Click "Dedicated Domain" or "Add Domain". [verify menu name]
27. Enter a subdomain of the Next Level domain, for example a "mail" subdomain. [Ray to set: domain for Next Level]
28. HighLevel shows DNS records. Copy each one.
29. In a new tab, log in to the domain registrar. Add each DNS record exactly as shown.
30. Back in HighLevel, click "Verify". [verify menu name] If it fails, wait and try again. DNS changes can take a while.
31. Set the default "from" name to "Ray Ahmadi | Next Level" and the from address on the new domain.
32. Set the reply-to address to an inbox someone reads.
33. Check that the unsubscribe link is switched on for marketing emails. [verify menu name]
34. In Settings > Business Profile or Email settings, confirm the mailing address shows in the email footer. [verify menu name]

## Part E. Stripe

**Stop here if Stripe verification is not finished. Come back to this part when it is.**

35. In the sub-account left menu, click "Payments". [verify menu name]
36. Click "Integrations". [verify menu name]
37. Next to Stripe, click "Connect". [verify menu name]
38. Log in to the verified Stripe account and approve the connection.
39. Confirm the status shows connected and in live mode, not test mode.
40. Create the first product: "Next Level Answer, Founding 10", $300, recurring monthly. [verify menu name] Get Ray's yes on the product wording before saving.
41. Note: client subscriptions sold through SaaS mode are set up in the agency view, in the SaaS configurator. That is covered in `saas-build-spec.md`. The connection in this part is for the checkout page inside the sales funnel. Which of the two Ray uses for the Founding 10: [verify in HighLevel]

## Part F. Calendar

42. In the left menu click "Calendars", then "Calendar Settings". [verify menu name]
43. Click "Create Calendar". Choose the simple one-to-one type. [verify menu name]
44. Name: "Next Level 15-minute call". Length: 15 minutes.
45. Assign it to Ray. (Ray's user is added in Part H. If Ray is not listed yet, do Part H first and come back.)
46. Set available hours. [Ray to set: hours Ray takes sales calls]
47. Connect Ray's Google or Outlook calendar so bookings do not clash. Ray must do this step himself while logged in as Ray.
48. Set the meeting location: phone call or video link. [Ray to set: phone or video for the 15-minute call]
49. Turn on the confirmation email. Leave text reminders off until the number is registered (step 23).
50. Save. Copy the calendar's booking link. You will send it back at the end.

## Part G. Load the snapshot

Do this only when the Next Level sales snapshot exists. If it does not exist yet, skip to Part H and come back.

51. Switch back to the agency view.
52. Click "Sub-Accounts". Find Next Level.
53. Open the three-dot menu or "Actions" on the Next Level row and choose "Load Snapshot". [verify menu name]
54. Pick the Next Level sales snapshot.
55. Choose which assets to load. Load everything on the first load.
56. If asked about conflicts, choose to skip items that already exist, so nothing made in Parts B to F is overwritten. [verify menu name]
57. Click "Proceed" or "Load". [verify menu name] Wait for it to finish.
58. Open the Next Level sub-account. Check that the pipeline "Next Level Sales" shows these stages in order: Lead, Audit sent, Call booked, Won, Onboarding, Live, At risk.
59. Check that every workflow arrived switched off (draft). Do not publish any workflow. Ray approves each one first.

## Part H. Users

60. In the sub-account, click Settings, then "My Staff" or "Team". [verify menu name]
61. Click "Add Employee" or "Add User". [verify menu name]
62. Add Ray: role Admin. Use Ray's email.
63. Add Diana: role Admin.
64. Add Nadiya: role User. Give access to Conversations, Contacts, Opportunities and Calendars. Leave Settings, Payments and Workflows off. [Ray to confirm: Nadiya's access level]
65. If Ray or Diana already have agency-level logins, HighLevel may ask to link the existing user instead of creating a new one. Choose to link. [verify menu name]
66. Ask each person to log in once and set their own password and two-step login.

## Part I. Final checks

67. Send one test email from the sub-account to Ray's own inbox. Check the from name, the mailing address in the footer and the unsubscribe link.
68. Call the new number from a mobile phone. Check it rings through to Ray.
69. Book a test slot on the 15-minute calendar. Check it lands on Ray's calendar. Cancel it.
70. Find the funnel in "Sites" > "Funnels" and copy its link, if the snapshot has been loaded. [verify menu name]

## Part J. The NL Demo sub-account

Approved by Ray, 2026-11-15. For Ray or Diana. What it is for is in `saas-build-spec.md` section 2a.

71. Switch to the agency view. Click "Sub-Accounts", then "Create Sub-Account". [verify menu name]
72. If the Next Level master snapshot exists, choose it. If it does not exist yet, choose the blank option and load the snapshot later, as in Part G. [verify menu name]
73. Name it "NL Demo". Time zone: Eastern (Toronto). Country: Canada. Leave any SaaS plan field empty.
74. Add made-up contacts only. No real person's name, number, email or call goes into this sub-account. Do not import any list into it.
75. Label every made-up record "sample".
76. Do not buy a phone number or connect a sending domain for it unless Ray asks. Nothing is sent from NL Demo to a real person.
77. Add Ray and Diana as Admin users.

## Done checklist

- [x] 1. Next Level sub-account exists. (Verified 2026-11-15: name "Next Level", location ID n0qwGpNQ3CShe8AIhyI0.)
- [ ] 2. Business profile complete: name, address, logo, time zone.
- [ ] 3. Phone number bought, named and ringing through.
- [ ] 4. Messaging registration filed (status: filed or approved).
- [ ] 5. Sending domain verified, from name "Ray Ahmadi | Next Level".
- [ ] 6. Test email shows the mailing address and a working unsubscribe link.
- [ ] 7. Stripe connected in live mode (or marked "waiting on verification").
- [ ] 8. "Next Level 15-minute call" calendar live and tied to Ray's calendar.
- [ ] 9. Snapshot loaded, pipeline stages correct, all workflows still off (or marked "snapshot not built yet").
- [ ] 10. Ray, Diana and Nadiya can each log in.
- [ ] 11. NL Demo sub-account created by Ray or Diana: named "NL Demo", made-up contacts only, every record labelled "sample". (Approved by Ray, 2026-11-15.)
- [ ] 12. Ray has said which list was imported into this sub-account on 2026-11-15, and no Ray Homes consumer contact is set to receive Next Level email.

## Send these back to Ray

Paste into one message. No client names, phone numbers or emails.

| Item | Value |
|---|---|
| Location ID | n0qwGpNQ3CShe8AIhyI0 (verified 2026-11-15) |
| Funnel URL (sales page) | |
| Calendar link (15-minute call) | |
| Checkout link (Founding 10) | Blocked until Stripe verification |
| Next Level phone number | |
| Sending domain and from address | |
| Messaging registration status | |
| NL Demo sub-account created (yes or no) | |
| Which list was imported on 2026-11-15 | |
| Anything that did not match these steps | |
