# GCP Setup for Treepolitics — Runbook

> **Resuming an in-flight setup?** The first attempt on 2026-05-01 hit two
> unanticipated GCP changes (DRS now on by default; v1/v2 org-policy UI
> bug). If you're picking up partway through, read
> [`gcp-setup-resume.md`](./gcp-setup-resume.md) first — it documents the
> exact resume point and provides a Cloud Shell paste-block that completes
> the blocked steps. This doc is the full procedural reference; the
> resume doc is the bookmark.

This document walks through the initial Google Cloud Platform setup for the
Treepolitics project. It is written as a literal step-by-step runbook:
follow it top to bottom, in order. When it is done, we will have:

- The `treepolitics.net` domain owned by Will on Spaceship.
- A Google Cloud **Organization** bound to `treepolitics.net`, owned by
  Will.
- A company **Billing Account** under Will's identity with the company
  card attached.
- A GCP **Project** `treepolitics-prod` linked to that billing account,
  ready to host Cloud Run + Cloud SQL.
- IAM roles granted to `amr@agtechgroup.solutions` at the organization
  level, so Amr can drive the actual migration without needing Will in the
  loop for every action.

## Two actors

This runbook has two people doing things. Every step below is labelled
with who performs it:

- 🧑‍💼 **Will** — owner of Treepolitics. Does the identity, billing, and
  ownership setup.
- 🛠️ **Amr** — operating as an external collaborator with the email
  `amr@agtechgroup.solutions` (not a `@treepolitics.net` account — see the
  "Who is Super Admin" note below).

## Who is Super Admin — and why Amr isn't

Google's identity system has two different "admin" layers that are easy to
confuse:

| Layer | Where you manage it | Who holds it here |
|---|---|---|
| **Cloud Identity Super Admin** — controls users, groups, domain settings, password/2FA policies | `admin.google.com` | **Will only** (as `admin@treepolitics.net`) |
| **GCP IAM Organization Administrator** — controls projects, Cloud Run, Cloud SQL, billing links, networking, all GCP resources | `console.cloud.google.com` | **Amr** (as `amr@agtechgroup.solutions`) |

Super Admin is a role on a **user inside the tenant**, so it can only be
held by `@treepolitics.net` users. Since Amr is not creating a
`@treepolitics.net` account, he cannot be Super Admin — and he does not
need to be. GCP IAM roles granted to his existing
`amr@agtechgroup.solutions` email cover 100% of the migration work.

**Bus-factor note:** Will is the sole Super Admin on the Treepolitics
Cloud Identity tenant. If Will is incapacitated, the tenant recovery path
is Google Support + the recovery email we set up in step 2. This is a
deliberate choice: Will owns the company, so tenant recovery and company
recovery are the same problem. If that calculus ever changes (e.g. Will
hires employees, or wants a second break-glass admin), we can revisit by
creating a dedicated `@treepolitics.net` user later.

---

## 0. Before you start — what you need in front of you

Gather these before touching anything. If any are missing, pause and
resolve them first — half-finished setup is harder to fix than delayed
setup.

- [ ] 🧑‍💼 **Will has a Spaceship account.** If not, he creates one at
      <https://www.spaceship.com> first. Free.
- [ ] 🧑‍💼 **Will's personal email address** (e.g. his Gmail). This will
      be used as the Cloud Identity recovery email and the billing /
      security notification address — because no mailbox on
      `treepolitics.net` will exist.
- [ ] 🧑‍💼 **Company credit card** for billing.
- [ ] 🧑‍💼 **2FA app** on Will's phone (Google Authenticator, 1Password,
      Authy). Google forces 2FA on Super Admin accounts on first login.
- [ ] 🧑‍💼 **Password manager** for storing the `admin@treepolitics.net`
      credentials. Do not email them to anyone.
- [ ] 🛠️ **Amr's email** `amr@agtechgroup.solutions` already works and has
      2FA enabled (it does — this is Amr's existing AG Tech Group account).

---

## 1. Transfer `treepolitics.net` from Amr to Will on Spaceship

**Who:** 🛠️ Amr initiates, 🧑‍💼 Will accepts.

### Why this step exists

Amr currently owns `treepolitics.net` in his personal Spaceship account.
For the setup to match the real ownership of the company, Will needs to
become the registrant of record *before* we create the Cloud Identity.
That way Will literally does every Google-side step himself on a domain
he owns, and there is never a period where the infra lives on someone
else's domain.

Spaceship supports **push transfers** (also called internal or account
transfers) between accounts within Spaceship. These are free, instant,
skip the 5–7 day ICANN transfer wait, and do not require unlocking the
domain or generating an EPP/auth code.

### Steps

1. 🛠️ Amr logs in to Spaceship and opens the management page for
   `treepolitics.net`.
2. 🛠️ Amr looks for the option to transfer the domain **to another
   Spaceship account** (the exact label varies — look for "Push to
   another account", "Transfer to another user", "Account transfer", or
   similar — *not* "Transfer out" or "Transfer to another registrar",
   which start a slow ICANN transfer). If you can't find it, Spaceship
   support can confirm the exact path.
3. 🛠️ Amr enters Will's Spaceship account email and submits.
4. 🧑‍💼 Will receives a notification in his Spaceship account and accepts
   the transfer.
5. 🧑‍💼 Will confirms in his Spaceship dashboard that `treepolitics.net`
   now appears under his domains.

### Verify the transfer

- [ ] 🧑‍💼 Will can see `treepolitics.net` in his Spaceship account.
- [ ] 🧑‍💼 Will can access the **DNS panel** for `treepolitics.net` —
      try opening the DNS / Nameservers section and confirming you can
      view existing records. This matters because the next step will
      require adding a DNS TXT record.
- [ ] 🛠️ Amr no longer sees `treepolitics.net` in his Spaceship account
      (confirms the push went through).

---

## 2. Create the Cloud Identity Free account on `treepolitics.net`

**Who:** 🧑‍💼 Will does all of this.

### Why this step exists

GCP's resource hierarchy is **Organization → Folders → Projects**.
Everything below the Organization — projects, billing links, IAM policies
— inherits from it. To get an Organization node, you need an *identity
provider* tied to a domain. Cloud Identity Free is Google's no-cost,
identity-only product (no Gmail, no Drive, no Workspace subscription —
just accounts and groups) that exists specifically to provide this.

### Important: what "creating the admin account" actually means

This is the single most confusing part of the process, so read it
carefully before clicking anything.

**Nothing `@treepolitics.net` exists in Google's systems right now.**
During the signup wizard, Will will be asked to *invent* a username for
the first admin account. He will type `admin`, and at that moment
`admin@treepolitics.net` comes into existence — but only as a **Google
login credential**, not as a mailbox.

| Layer | After signup |
|---|---|
| DNS — the domain | `treepolitics.net`, owned by Will at Spaceship |
| Google Identity — the *login* | `admin@treepolitics.net` — logs into `admin.google.com` and GCP |
| Mail — the *mailbox* | **Nothing.** No MX records, no inbox, emails to that address bounce |

The three layers are independent. Cloud Identity only touches the middle
one. The bottom layer (mail) stays empty, and GCP does not care.

Because mail is empty, Google's automated emails to
`admin@treepolitics.net` (password resets, security alerts, budget
notifications) would bounce and be lost. We fix this in two ways below:

1. A **recovery email** on the admin account pointing at Will's personal
   email (handled in this step).
2. **Explicit notification email recipients** on budget alerts and
   billing (handled in step 3).

### Steps

1. 🧑‍💼 Will opens <https://workspace.google.com/gcpidentity/signup?sku=identitybasic>
   in an **incognito window**. Incognito prevents accidentally tying the
   new tenant to his personal Google session. Note: the older
   `cloud.google.com/identity` link no longer exposes the Free signup
   directly — Google has moved it under Workspace marketing and the page
   now shows only "Contact us" / "Try premium." The URL above is the
   durable path; the `?sku=identitybasic` query parameter is what selects
   the $0 Free edition rather than a paid Workspace plan.
2. 🧑‍💼 Click **Get started free** (or **Start free trial** — Google
   rotates the button text; the product is "Cloud Identity Free Edition",
   and it is $0).
3. 🧑‍💼 On the "About your business" screen, enter:
   - **Business name:** `Treepolitics`
   - **Number of employees:** 1 (or the honest bracket; Cloud Identity
     Free is $0 regardless).
   - **Region:** the country Treepolitics operates from.
4. 🧑‍💼 On the "Contact info" screen, enter Will's name and **Will's
   personal email address** (his Gmail, not anything `@treepolitics.net`).
   This is only used by Google to send setup confirmations — it is not
   the admin account. It *must* be a real, working mailbox.
5. 🧑‍💼 On the "About your domain" screen, choose **Yes, I have a domain
   I can use**, then enter `treepolitics.net`.
6. 🧑‍💼 On the "Create your admin account" screen:
   - **Username:** `admin` (will become `admin@treepolitics.net`).
   - **Password:** generate a strong password in a password manager and
     save it immediately. Do not reuse an existing password.
7. 🧑‍💼 Agree to the terms and click **Agree and continue**. Will is now
   logged in to `admin.google.com` — this is a different URL from the GCP
   console. Bookmark both.

### Verify the domain (DNS TXT record)

Google will prompt Will to prove he owns `treepolitics.net`. It displays
a TXT record that looks like
`google-site-verification=<long-random-string>`.

1. 🧑‍💼 In a new tab, open the Spaceship DNS panel for
   `treepolitics.net`.
2. 🧑‍💼 Add a **TXT record** with:
   - **Host / Name:** `@` (the apex of the domain; Spaceship may label
     this "root" or let you leave it blank).
   - **Value:** the full `google-site-verification=...` string Google
     gave you. Copy it exactly — no extra quotes.
   - **TTL:** default (usually 3600 or 1 hour).
3. 🧑‍💼 Save the DNS change. Propagation is usually under a minute at
   Spaceship, but can take up to an hour.
4. 🧑‍💼 Back in the Google setup wizard, click **Verify**. If it fails,
   wait two minutes and try again. If it still fails after 15 minutes,
   use <https://toolbox.googleapps.com/apps/dig/#TXT/> to confirm the
   TXT record is actually live, then retry.

When verification succeeds, **the Organization resource is created
automatically**. There is now a GCP org node named `treepolitics.net`.

### Set the recovery email (critical — do not skip)

Because `admin@treepolitics.net` is not a real mailbox, any Google
password recovery or security alert sent to it will bounce. Without a
recovery email, Will can get permanently locked out of the tenant.

1. 🧑‍💼 In `admin.google.com`, go to **Directory → Users**.
2. 🧑‍💼 Click on `admin@treepolitics.net`.
3. 🧑‍💼 Expand **Security** → find **Recovery information** (sometimes
   labelled **Account recovery**).
4. 🧑‍💼 Enter **Will's personal email** as the recovery email. Also add
   his phone number as a recovery phone if desired.
5. 🧑‍💼 Save.

### Turn on 2FA for the admin account

1. 🧑‍💼 In `admin.google.com`, go to **Security → Authentication →
   2-step verification**.
2. 🧑‍💼 Turn on enforcement for the admin account.
3. 🧑‍💼 Log out and log back in; you will be prompted to enroll a second
   factor. Use the authenticator app from step 0.

---

## 3. Create the Billing Account

**Who:** 🧑‍💼 Will creates, then grants 🛠️ Amr access.

### Why this step exists

In GCP, a **Billing Account** is a resource separate from the
Organization and from Projects. It holds the payment method and the
invoice history. Projects are *linked* to a billing account, and can be
re-linked later without downtime. Keeping billing as its own resource is
what lets Will rotate payment methods, set budgets, and see spend
independently of who administers the infra.

### Create the billing account

1. 🧑‍💼 Will goes to <https://console.cloud.google.com/billing> and logs
   in with `admin@treepolitics.net`.
2. 🧑‍💼 In the top bar, make sure the **organization selector** shows
   `treepolitics.net`. If it says "No organization", stop — something
   went wrong in step 2 and the project would be created as an orphan.
3. 🧑‍💼 Click **Create account**.
4. 🧑‍💼 Fill in:
   - **Name:** `Treepolitics — Main`
   - **Country:** the country Treepolitics bills from. **This cannot be
     changed later** without creating a new billing account, so
     double-check it matches the company's legal address.
   - **Currency:** auto-selected from country; confirm it is correct.
5. 🧑‍💼 Continue to the **payment information** step and enter the
   company credit card details. If there is a tax ID / VAT number, enter
   it here — adding it later is harder.
6. 🧑‍💼 Click **Submit and enable billing**.

### Grant Amr access to billing

1. 🧑‍💼 Still under **Billing**, open the new billing account.
2. 🧑‍💼 Go to **Account management** (sometimes called **Permissions**)
   in the left nav.
3. 🧑‍💼 Click **Add principal** (or **+ Add member**).
4. 🧑‍💼 Enter `amr@agtechgroup.solutions`.
5. 🧑‍💼 In the role dropdown, choose **Billing Account User**
   (`roles/billing.user`). *Not* Billing Account Administrator — User
   lets Amr link projects to this billing account without giving him
   permission to edit Will's payment method.
6. 🧑‍💼 Click **Save**.

### Route budget alerts to real inboxes

Google's default behavior is to send budget notifications to billing
admins by email. Since `admin@treepolitics.net` bounces, Will would
silently miss a "you just spent $500" alert. Fix this now by creating a
budget with explicit recipients:

1. 🧑‍💼 Still in **Billing**, go to **Budgets & alerts → Create budget**.
2. 🧑‍💼 Name: `Treepolitics monthly — alert only`.
3. 🧑‍💼 Scope: all projects linked to this billing account.
4. 🧑‍💼 Amount: pick a ceiling that would alert you before anything
   runaway happens — e.g. $100 / month for now. This is an **alert
   threshold, not a hard cap** — GCP does not auto-stop services when
   you hit it.
5. 🧑‍💼 Under **Actions → Manage notifications → Email recipients**,
   explicitly add:
   - Will's personal email
   - `amr@agtechgroup.solutions`
6. 🧑‍💼 Save.

---

## 4. Grant Amr organization-level IAM roles

**Who:** 🧑‍💼 Will.

### Why this step exists

Step 3 gave Amr access to billing. He still needs roles on the *GCP
resource layer* so he can create projects, manage IAM, and run the
actual migration. Granting these **at the Organization level** means he
inherits them on every project in the org automatically — including
projects that do not exist yet. That is critical, because we are about
to create `treepolitics-prod` in step 5, and we do not want to re-grant
roles on each future project.

### Will first grants himself GCP IAM roles (bootstrap)

This sub-step is unintuitive and easy to miss. **Cloud Identity Super
Admin (`admin@treepolitics.net`) does not automatically come with GCP
IAM roles on the org.** The two role surfaces are deliberately
separated by Google: Super Admin manages the *tenant* (users, groups,
domain settings), while GCP IAM roles manage *resources* (projects,
billing links, org policies). Without an explicit self-grant, Will
will see "You need additional access" on the IAM and Org Policies
pages and won't be able to grant Amr anything.

There is a built-in **bootstrap path**: Super Admins always retain
implicit access to the GCP IAM page on the org node, specifically so
they can grant themselves (or someone else) explicit IAM roles.
Without this, a fresh tenant could never get its first GCP admin —
chicken and egg. Use it now:

1. 🧑‍💼 Will goes to <https://console.cloud.google.com/iam-admin/iam>.
2. 🧑‍💼 Confirms the top selector shows `treepolitics.net` (the org).
3. 🧑‍💼 **Grant access** → New principal: `admin@treepolitics.net`
   (himself).
4. 🧑‍💼 Adds these two roles:
   - **Organization Administrator** (`roles/resourcemanager.organizationAdmin`)
     — to manage IAM bindings on the org and create folders.
   - **Organization Policy Administrator** (`roles/orgpolicy.policyAdmin`)
     — to edit org policies, including the DRS relaxation in the next
     section.
5. 🧑‍💼 Saves. Hard-refreshes the page to clear the auth cache.

Now Will can both edit org policies *and* grant Amr the roles below.

### Steps to grant Amr

1. 🧑‍💼 Go to <https://console.cloud.google.com/iam-admin/iam>.
2. 🧑‍💼 In the top bar, change the resource scope from any project to
   the **Organization**. This is the most common source of mistakes: if
   you grant roles while a project is selected, the roles do not
   cascade. **Make sure the selector shows `treepolitics.net`, not a
   project.**
3. 🧑‍💼 Click **Grant access** (sometimes labelled **+ Add**).
4. 🧑‍💼 In **New principals**, enter `amr@agtechgroup.solutions`.
5. 🧑‍💼 Under **Assign roles**, add each of the following, using **Add
   another role**:
   - **Organization Administrator**
     (`roles/resourcemanager.organizationAdmin`) — manage IAM at the
     org, create folders, edit org policies.
   - **Project Creator**
     (`roles/resourcemanager.projectCreator`) — create new projects
     under the org without asking Will.
   - **Organization Role Administrator**
     (`roles/iam.organizationRoleAdmin`) — define custom IAM roles if
     needed later.
   - **Folder Admin**
     (`roles/resourcemanager.folderAdmin`) — organize projects into
     folders (e.g. `prod/`, `experiments/`) later.
6. 🧑‍💼 Click **Save**.

> **Do not grant `roles/owner` at the org level.** Owner is broader in
> some ways and narrower in others than the combination above; the four
> roles listed are the recommended pattern for a trusted platform admin
> and are easier to audit.

### ⚠️ Domain Restricted Sharing is now ON BY DEFAULT — you must relax it

GCP has an org policy called
`iam.allowedPolicyMemberDomains` — **Domain Restricted Sharing (DRS)**.
When enforcing, it restricts IAM principals to a list of allowed Cloud
Identity customer IDs. Because Amr operates as `amr@agtechgroup.solutions`
(outside the `treepolitics.net` tenant), enforcement blocks every IAM
grant to him.

**This default flipped sometime in 2024–2025** as part of Google's
secure-by-default rollout. New Cloud Identity orgs ship with DRS already
enforcing `allowedValues: [<your own customer ID>]`. The first IAM grant
to Amr will fail with:

> The 'Domain Restricted Sharing' organization policy
> (constraints/iam.allowedPolicyMemberDomains) is enforced. Only
> principals in allowed domains can be added as principals in the policy.

**The Org Policies UI cannot reliably disable this.** A v1/v2 API
mismatch in the org-policy service means the UI's "Override → Replace
→ Allow all" save displays as "Inactive" while the API continues to
enforce the original allowed values. The only durable workaround is
to write the policy via gcloud v2 YAML (see Appendix B for full
diagnosis). Quick fix in Cloud Shell:

```bash
ORG_ID=$(gcloud organizations list --format="value(ID)" | head -1)
cat > /tmp/drs-allow-all.yaml <<EOF
name: organizations/${ORG_ID}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - allowAll: true
EOF
gcloud org-policies set-policy /tmp/drs-allow-all.yaml

# Verify — must show "allowAll: true", no allowedValues
gcloud org-policies describe iam.allowedPolicyMemberDomains \
  --organization=$ORG_ID
```

After verification, proceed with granting Amr the four IAM roles above —
the constraint is no longer enforcing.

**Hardening (within ~1 week of go-live):** `allowAll: true` is
deliberately permissive. The recommended posture is to switch back to
an explicit allowlist containing both Cloud Identity customer IDs:
`treepolitics.net`'s own (auto-populated) plus
`agtechgroup.solutions`' (Amr provides). See
[`gcp-setup-resume.md`](./gcp-setup-resume.md) for the allowlist YAML.

### Verify Amr has access

1. 🛠️ Amr opens <https://console.cloud.google.com> and logs in with
   `amr@agtechgroup.solutions`.
2. 🛠️ In the top bar, open the organization selector and confirm
   `treepolitics.net` appears. Select it.
3. 🛠️ Navigate to **IAM & Admin → IAM** and confirm the four roles are
   listed against his email.
4. 🛠️ Reply to Will confirming access works before proceeding to step 5.

---

## 5. Create the `treepolitics-prod` project and link billing

**Who:** 🛠️ Amr (using his new Project Creator role). If Amr hits any
snag, 🧑‍💼 Will can do this step instead.

### Why one project, no staging

Best practice is one GCP project per environment. For now, Treepolitics
will have only `treepolitics-prod`. We are deliberately deferring a
staging project until there is real user data that would benefit from
a pre-prod rehearsal environment — at which point `treepolitics-staging`
will be added as a sibling project under the same org.

Once there are real users, creating staging is **strongly recommended
before** attempting any non-trivial schema migration, secret rotation,
or Cloud Run config change. Production data recovery is expensive; a
staging rehearsal is free.

### Steps

1. 🛠️ Go to <https://console.cloud.google.com/projectcreate>.
2. 🛠️ Fill in:
   - **Project name:** `treepolitics-prod`
   - **Project ID:** the console will suggest one based on the name.
     Project IDs are **globally unique across all of GCP** and
     **cannot be changed later**, so pick deliberately. Recommended:
     `treepolitics-prod` if available; otherwise add a short suffix like
     `treepolitics-prod-01`.
   - **Organization:** select `treepolitics.net`. If this dropdown says
     "No organization", stop — something is wrong with the IAM grant
     from step 4.
   - **Location (parent):** select the organization itself. Folders can
     be added later.
3. 🛠️ Click **Create**.
4. 🛠️ Once the project exists, go to **Billing** in the left nav (or
   <https://console.cloud.google.com/billing/linkedaccount>) and link it
   to the `Treepolitics — Main` billing account created in step 3.

---

## 6. Verification checklist

Before declaring setup complete, confirm each item below. If any is
wrong, fix it now — it is much cheaper than fixing it later.

- [ ] Will is the registrant of `treepolitics.net` at Spaceship.
- [ ] `treepolitics.net` Organization exists in the GCP console
      organization selector.
- [ ] `admin@treepolitics.net` can log in to `admin.google.com` with 2FA
      enabled.
- [ ] `admin@treepolitics.net` has Will's personal email set as the
      recovery email.
- [ ] Billing account `Treepolitics — Main` exists, has a valid payment
      method, and is tied to the `treepolitics.net` org.
- [ ] `amr@agtechgroup.solutions` is listed as a **Billing Account User**
      on the billing account.
- [ ] A monthly budget alert exists, with Will's personal email and
      `amr@agtechgroup.solutions` as explicit notification recipients.
- [ ] At the organization scope in IAM, `amr@agtechgroup.solutions` has
      all four roles: Organization Administrator, Project Creator,
      Organization Role Administrator, Folder Admin.
- [ ] `iam.allowedPolicyMemberDomains` (Domain Restricted Sharing) is
      **not** enabled on the org.
- [ ] Amr has logged into the GCP console and confirmed he can see
      `treepolitics.net` in the org selector.
- [ ] `treepolitics-prod` project exists, is a child of
      `treepolitics.net` (not an orphan), and is linked to the billing
      account.

---

## 7. What happens next (for context)

Once the checklist above is green, initial setup is complete. The next
phase is the actual migration of the Treepolitics API, which Amr will
drive. For Will's awareness, the upcoming work will use these GCP
services inside `treepolitics-prod`:

- **Cloud Run** — will host the FastAPI container built from the
  existing `Dockerfile`.
- **Cloud SQL for PostgreSQL** — will replace the local `docker-compose`
  postgres instance. The `DATABASE_URL` env var will point at it via the
  Cloud SQL Auth Proxy.
- **Secret Manager** — will hold `SECRET_KEY`, `DATABASE_URL`, and any
  other secrets, injected into Cloud Run at deploy time instead of
  living in a `.env` file.
- **Artifact Registry** — will host the built Docker images that Cloud
  Run pulls from.
- **Cloud Build** (or GitHub Actions) — will build and push images on
  merges to `main`.

None of these require additional setup from Will right now; they will
be enabled per-project by Amr as the migration proceeds.

---

## Appendix A — Optional: email forwarding on `treepolitics.net`

Not needed for GCP. Included here in case Will wants real email on the
domain later.

If Treepolitics ever needs `@treepolitics.net` email to actually work
(e.g. `hello@treepolitics.net` reaching Will), there are three cheap
options, none of which interfere with the Cloud Identity setup above:

- **Spaceship email forwarding** — usually free. Forwards addresses like
  `hello@treepolitics.net` to Will's personal inbox. Set up in the
  Spaceship domain panel. Does not interfere with Cloud Identity at
  all — forwarding happens at the MX layer, identity happens at the
  verification layer.
- **Cloudflare Email Routing** — free, but requires moving DNS to
  Cloudflare first.
- **Upgrade to Google Workspace** — $6/user/month, gives real mailboxes
  at `@treepolitics.net` and reuses the same identity tenant that Cloud
  Identity already set up. The `admin@treepolitics.net` login survives
  the upgrade unchanged.

---

## Appendix B — Troubleshooting

**"I added the TXT record at Spaceship but Google verification keeps
failing."**
Use <https://toolbox.googleapps.com/apps/dig/#TXT/> to query the TXT
record directly. If it does not show up, the DNS change has not
propagated or was saved incorrectly (common mistake: pasting it into the
wrong domain, or adding extra quotes around the value). If it does show
up but Google still will not verify, double-check you pasted the exact
string Google generated — each domain gets a unique one.

**"I don't see the Organization in the GCP console after verifying the
domain."**
Wait 2–3 minutes and refresh. If still missing, log out and back in —
the org node sometimes does not appear in an existing session. If still
missing after 10 minutes, go to `admin.google.com → Account → Domains`
and confirm the domain is listed as **Verified**.

**"I created the billing account but the project says 'billing is
disabled'."**
Projects are not auto-linked to billing. Go to the project → **Billing**
in the left nav → **Link a billing account**, and select
`Treepolitics — Main`.

**"Amr says he can't see the organization in the GCP console."**
He almost certainly selected a project in the top bar instead of the
org. Tell him to click the top-bar selector, switch the filter to
**Organization**, and pick `treepolitics.net`. If that still does not
work, re-check step 4 — IAM roles must be granted while the
*Organization* is selected as the scope, not a project.

**"Will forgot the `admin@treepolitics.net` password and can't log in."**
Use the recovery email flow: on the Google login screen, click **Forgot
password**. The recovery code will be sent to Will's personal email (the
one we set in step 2's "Set the recovery email" section). This is why
that step is marked critical.

**"Amr lost access to the org after a security hardening change."**
Most likely cause: someone tightened the
`iam.allowedPolicyMemberDomains` (Domain Restricted Sharing) org policy.
Will, as Super Admin of the tenant, can disable it via Cloud Shell —
**not** via the UI; see the next entry. Once disabled, Amr's access is
immediately restored — the IAM bindings themselves were never deleted.

**"The Org Policies UI says DRS is Inactive but IAM grants still fail
with the DRS error."**
Real product bug, not user error. Google's org-policy service has two
API versions running side by side (`v1` and `v2`); the console writes
to one shape and the enforcement engine reads from the other for this
constraint. The UI's "Override → Replace → Allow all" save reports
success and renders the policy as "Inactive," but
`gcloud org-policies describe iam.allowedPolicyMemberDomains
--organization=$ORG_ID` reveals the API still has
`allowedValues: [<your customer ID>]`. The reliable workaround is to
write the policy directly via gcloud v2 YAML:

```bash
ORG_ID=$(gcloud organizations list --format="value(ID)" | head -1)
cat > /tmp/drs-allow-all.yaml <<EOF
name: organizations/${ORG_ID}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - allowAll: true
EOF
gcloud org-policies set-policy /tmp/drs-allow-all.yaml
```

After this, re-run the IAM grant. The policy may be patched in a future
GCP release; verify the workaround is still needed before assuming.

**"`gcloud organizations list` returns nothing or errors with
'API not enabled'."**
Cloud Shell auto-creates a personal project for each user (something
like `angular-shore-XXXXXX-XX`); some org-related APIs need to be
enabled on that project even when targeting org-level resources.
Either accept the prompt to enable `orgpolicy.googleapis.com` /
`cloudresourcemanager.googleapis.com` when gcloud asks, or run
`gcloud services enable cloudresourcemanager.googleapis.com
orgpolicy.googleapis.com` on the Cloud Shell project explicitly.

**"The console UI says I need additional access on Org Policies even
as `admin@treepolitics.net`."**
Cloud Identity Super Admin and GCP IAM Organization Administrator are
separate roles on separate systems. Super Admin doesn't auto-grant
GCP roles. Use the bootstrap path: as Super Admin you retain implicit
access to the GCP IAM page on the org, where you can grant yourself
`roles/resourcemanager.organizationAdmin` and
`roles/orgpolicy.policyAdmin`. See the "Will first grants himself"
sub-section in step 4 above.
