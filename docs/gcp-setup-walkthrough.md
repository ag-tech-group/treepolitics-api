# Treepolitics GCP Setup — Walkthrough

A short step-by-step checklist for Amr and Will to work through together
in one sitting. Approximate time: 30 minutes.

> **Picking up mid-flight?** The first attempt at this walkthrough on
> 2026-05-01 hit two unanticipated GCP changes (DRS now on by default;
> v1/v2 org-policy UI bug). If you're resuming partway through, read
> [`gcp-setup-resume.md`](./gcp-setup-resume.md) first — it documents
> exactly where things left off and provides a Cloud Shell paste-block
> that completes the blocked steps.

For background, rationale, and troubleshooting, see the detailed doc at
`docs/gcp-setup.md`.

## Who does what

- **[WILL]** — Will performs this step.
- **[AMR]**  — Amr performs this step.
- **[BOTH]** — confirm together before moving on.

---

## Before you begin

Have these ready before starting the clock:

- [ ] **[WILL]** Spaceship account (create one at spaceship.com if needed).
- [ ] **[WILL]** A personal email (e.g. Gmail) you can receive mail at.
- [ ] **[WILL]** The company credit card.
- [ ] **[WILL]** An authenticator app on your phone (Google Authenticator,
      1Password, Authy) — Google will force 2FA during setup.
- [ ] **[WILL]** A password manager entry ready to store new credentials.
- [ ] **[AMR]**  Logged in to your Spaceship account (the one that owns
      `treepolitics.net` right now).
- [ ] **[AMR]**  Logged in to `amr@agtechgroup.solutions` in a browser.

---

## Phase 1 — Transfer `treepolitics.net` to Will (5 minutes)

**Goal:** Will becomes the registrant of `treepolitics.net` on Spaceship.

1. **[AMR]**  In Spaceship, open the management page for
   `treepolitics.net`.
2. **[AMR]**  Find the option to **push / transfer to another Spaceship
   account** (look for "Push to another account", "Transfer to another
   user", or "Account transfer" — *not* "Transfer out to another
   registrar", which is the slow ICANN route).
3. **[AMR]**  Enter Will's Spaceship account email. Submit.
4. **[WILL]** Open the notification in your Spaceship account and
   **accept** the transfer.
5. **[BOTH]** Confirm:
   - [ ] **[WILL]** `treepolitics.net` shows up under his domains.
   - [ ] **[WILL]** Can open the DNS panel and see existing records.
   - [ ] **[AMR]**  `treepolitics.net` no longer appears in his Spaceship
     account.

---

## Phase 2 — Create the Cloud Identity on `treepolitics.net` (10 minutes)

**Goal:** Will creates a Google Cloud Identity Free account tied to
`treepolitics.net`. This gives us the GCP Organization.

### Important to understand before starting

Will is about to **invent** an admin username. Right now nothing
`@treepolitics.net` exists anywhere in Google. During signup, Will types
`admin` and — at that moment — `admin@treepolitics.net` is created as a
**Google login credential only**, not a mailbox. Emails sent to that
address will bounce, forever, until/unless we set up email separately.
That is fine; GCP does not need mail delivery to work.

### Steps

1. **[WILL]** Open `https://workspace.google.com/gcpidentity/signup?sku=identitybasic`
   in an **incognito window** (prevents tangling with any existing Google
   login). The marketing page at `cloud.google.com/identity` no longer
   surfaces the Free signup directly — Google has moved it under Workspace
   marketing. The `?sku=identitybasic` query parameter is what selects
   the $0 Free edition rather than a paid Workspace plan.
2. **[WILL]** Click **Get started free** (or "Start free trial" — the
   product is Cloud Identity *Free Edition*, $0).
3. **[WILL]** Fill in the business info:
   - Business name: `Treepolitics`
   - Employees: 1
   - Region: your country
4. **[WILL]** Contact info: use **your personal email** (Gmail). This is
   just for setup confirmations — it is not the admin account.
5. **[WILL]** Domain: enter `treepolitics.net`, confirm "Yes, I have a
   domain I can use".
6. **[WILL]** Create the admin account:
   - Username: `admin` → becomes `admin@treepolitics.net`
   - Password: generate a strong one and **save it in your password
     manager immediately**.
7. **[WILL]** Agree and continue. You are now in `admin.google.com`.
   Bookmark this URL.

### Verify the domain via DNS

Google will show a TXT record to add.

1. **[WILL]** Open a new tab → Spaceship DNS panel for
   `treepolitics.net`.
2. **[WILL]** Add a **TXT record**:
   - Host / Name: `@` (or blank — the apex of the domain)
   - Value: paste the full `google-site-verification=...` string **exactly**
   - TTL: default
3. **[WILL]** Save. Wait ~1 minute for propagation.
4. **[WILL]** Back in the Google setup tab, click **Verify**. Retry if
   it fails the first time.

- [ ] **[WILL]** Google confirms the domain is verified.
- [ ] **[WILL]** The organization `treepolitics.net` now exists.

### Set the recovery email (CRITICAL — do not skip)

Because `admin@treepolitics.net` is not a real mailbox, password resets
would bounce without this.

1. **[WILL]** In `admin.google.com` → **Directory → Users**.
2. **[WILL]** Click `admin@treepolitics.net`.
3. **[WILL]** Expand **Security → Recovery information**.
4. **[WILL]** Enter your personal email as the recovery email. Add your
   phone number as a recovery phone if desired.
5. **[WILL]** Save.

- [ ] **[WILL]** Recovery email is set to your personal email.

### Enable 2FA

1. **[WILL]** In `admin.google.com` → **Security → Authentication →
   2-step verification**.
2. **[WILL]** Turn on enforcement for the admin account.
3. **[WILL]** Log out, log back in. Enroll your authenticator app when
   prompted.

- [ ] **[WILL]** 2FA is active on `admin@treepolitics.net`.

---

## Phase 3 — Create the billing account (5 minutes)

**Goal:** A billing account exists under Will's identity, and Amr has
`Billing Account User` access on it.

### Create the billing account

1. **[WILL]** Go to `console.cloud.google.com/billing`. Log in as
   `admin@treepolitics.net` if prompted.
2. **[WILL]** In the top bar, confirm the **organization selector**
   shows `treepolitics.net`. If it says "No organization", stop — Phase 2
   did not complete correctly.
3. **[WILL]** Click **Create account**.
4. **[WILL]** Fill in:
   - Name: `Treepolitics — Main`
   - Country: Treepolitics's billing country (**cannot be changed later**)
   - Currency: auto-selected, confirm it is correct
5. **[WILL]** Payment information: enter the company card. Include tax
   ID / VAT if applicable (harder to add later).
6. **[WILL]** Click **Submit and enable billing**.

- [ ] **[WILL]** Billing account `Treepolitics — Main` exists.

### Grant Amr access

1. **[WILL]** In **Billing**, open the new account.
2. **[WILL]** Go to **Account management** (sometimes called
   **Permissions**) in the left nav.
3. **[WILL]** Click **Add principal**.
4. **[WILL]** Enter `amr@agtechgroup.solutions`.
5. **[WILL]** Role: **Billing Account User** (`roles/billing.user`) —
   *not* Administrator. User lets Amr link projects without giving him
   the ability to edit Will's payment method.
6. **[WILL]** Save.

- [ ] **[WILL]** `amr@agtechgroup.solutions` appears as a Billing
      Account User.

### Create a budget alert

Because `admin@treepolitics.net` bounces, we need to explicitly route
budget notifications to real inboxes.

1. **[WILL]** In **Billing → Budgets & alerts**, click **Create budget**.
2. **[WILL]** Name: `Treepolitics monthly — alert only`.
3. **[WILL]** Scope: all projects on this billing account.
4. **[WILL]** Amount: pick a ceiling that would alert you before
   anything runaway — e.g. **$100 / month** for now. This is an
   alert threshold only — GCP does not auto-stop services when you hit
   it.
5. **[WILL]** Actions → **Manage notifications → Email recipients**,
   explicitly add:
   - Will's personal email
   - `amr@agtechgroup.solutions`
6. **[WILL]** Save.

- [ ] **[WILL]** Budget exists with both emails as notification
      recipients.

---

## Phase 4 — Grant Amr IAM roles at the organization level (3 minutes)

**Goal:** Amr has organization-level admin on GCP resources via his
existing `amr@agtechgroup.solutions` email.

### 4a — Will first grants himself the GCP IAM roles he'll need

Cloud Identity Super Admin (`admin@treepolitics.net`) does **not**
automatically come with GCP IAM roles on the org. Without an explicit
self-grant, Will sees "You need additional access" on the IAM and
Org Policies pages and can't grant Amr anything. Bootstrap path:

1. **[WILL]** Go to `console.cloud.google.com/iam-admin/iam`.
2. **[WILL]** Confirm the top selector shows `treepolitics.net` (the
   org, not a project). Super Admins always have implicit access to
   this page even with no IAM bindings — that's how the bootstrap works.
3. **[WILL]** **Grant access** → New principal: `admin@treepolitics.net`
   (himself). Add these roles:
   - **Organization Administrator** (`roles/resourcemanager.organizationAdmin`)
   - **Organization Policy Administrator** (`roles/orgpolicy.policyAdmin`)
4. **[WILL]** Save. Wait ~30 seconds, hard-refresh the page.

### 4b — Grant Amr the four org-level roles

1. **[WILL]** Go to `console.cloud.google.com/iam-admin/iam`.
2. **[WILL]** In the top bar, change the resource scope to the
   **Organization** (`treepolitics.net`). **This is the most common
   mistake in the whole setup — if you grant roles while a project is
   selected, they do not cascade.** Make sure the selector shows
   `treepolitics.net`, not a project.
3. **[WILL]** Click **Grant access**.
4. **[WILL]** New principal: `amr@agtechgroup.solutions`
5. **[WILL]** Add these four roles (use **Add another role** between
   each):
   - [ ] **Organization Administrator**
         (`roles/resourcemanager.organizationAdmin`)
   - [ ] **Project Creator**
         (`roles/resourcemanager.projectCreator`)
   - [ ] **Organization Role Administrator**
         (`roles/iam.organizationRoleAdmin`)
   - [ ] **Folder Admin**
         (`roles/resourcemanager.folderAdmin`)
6. **[WILL]** Save.

### Verify Amr can access the org

1. **[AMR]**  Open `console.cloud.google.com` in your own browser and
   log in as `amr@agtechgroup.solutions`.
2. **[AMR]**  Click the organization selector in the top bar. Pick
   `treepolitics.net`.
3. **[AMR]**  Navigate to **IAM & Admin → IAM**. Confirm your email
   shows the four roles listed above.

- [ ] **[AMR]**  Can see `treepolitics.net` in the org selector.
- [ ] **[AMR]**  All four roles appear against his principal.

**⚠️ Domain Restricted Sharing is now ON BY DEFAULT for new Cloud Identity
orgs** (this changed sometime in 2024–2025 as part of Google's
"secure-by-default" rollout). The policy `iam.allowedPolicyMemberDomains`
will already be enforcing `allowedValues: [<your customer ID>]`, which
blocks IAM grants to external principals — including Amr's
`amr@agtechgroup.solutions`. You'll hit a "Domain Restricted Sharing is
enforced" error the first time you try to add him.

**⚠️ The Org Policies UI is currently buggy on this constraint.** The
"Override → Replace → Allow all" save renders the policy as "Inactive"
but a v1/v2 API mismatch means enforcement continues. Do not waste time
fighting the UI — relax the policy via gcloud Cloud Shell instead:

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

Verify with `gcloud org-policies describe iam.allowedPolicyMemberDomains
--organization=$ORG_ID` — must show `spec.rules: [- allowAll: true]`.

This leaves DRS off entirely. As a hardening pass within a week, swap
`allowAll: true` for an explicit allowlist of both Cloud Identity customer
IDs (treepolitics.net's own + agtechgroup.solutions' for Amr). See
[`gcp-setup-resume.md`](./gcp-setup-resume.md) for the allowlist YAML.

---

## Phase 5 — Create the `treepolitics-prod` project (3 minutes)

**Goal:** The first (and for now, only) project exists and is linked
to billing.

1. **[AMR]**  Go to `console.cloud.google.com/projectcreate`.
2. **[AMR]**  Fill in:
   - **Project name:** `treepolitics-prod`
   - **Project ID:** `treepolitics-prod` if available, otherwise add a
     short suffix like `-01`. **IDs are globally unique and cannot be
     changed later.**
   - **Organization:** `treepolitics.net`. If it says "No organization",
     stop — Phase 4 did not complete correctly.
   - **Location:** the organization itself (no folder for now).
3. **[AMR]**  Click **Create**.
4. **[AMR]**  Open the new project → **Billing** in the left nav → **Link
   a billing account** → select `Treepolitics — Main`.

- [ ] **[AMR]**  `treepolitics-prod` exists under `treepolitics.net`.
- [ ] **[AMR]**  `treepolitics-prod` is linked to `Treepolitics — Main`.

---

## Final checklist

Tick each before declaring the walkthrough complete. If any fails, see
`docs/gcp-setup.md` Appendix B for troubleshooting.

- [ ] Will is the registrant of `treepolitics.net` on Spaceship.
- [ ] `treepolitics.net` organization appears in the GCP org selector.
- [ ] `admin@treepolitics.net` has a working 2FA setup.
- [ ] `admin@treepolitics.net` has Will's personal email as its recovery
      email.
- [ ] Billing account `Treepolitics — Main` exists and has a valid card.
- [ ] `amr@agtechgroup.solutions` is a `Billing Account User`.
- [ ] Budget alert exists with Will's personal email and
      `amr@agtechgroup.solutions` as recipients.
- [ ] `amr@agtechgroup.solutions` has the four IAM roles at the org
      scope.
- [ ] Amr has logged in and confirmed he can see `treepolitics.net`.
- [ ] `treepolitics-prod` exists, parented to the org, linked to
      billing.
- [ ] Domain Restricted Sharing is **not** enabled on the org.

---

## If something goes wrong

Pause the walkthrough and open `docs/gcp-setup.md` → Appendix B.
Common issues:

- **DNS TXT verification fails:** use
  `toolbox.googleapps.com/apps/dig/#TXT/` to confirm the record is live,
  then retry.
- **Org does not appear in console:** log out / log back in — new orgs
  sometimes do not appear in an existing session.
- **Amr cannot see the org:** he most likely has a project selected in
  the top bar, not the org — switch the selector filter to
  "Organization".
- **Will forgets the admin password:** use "Forgot password" on the
  login screen; recovery code goes to his personal email via the
  recovery email set in Phase 2.

---

**Next session (no Will needed):** Amr begins the actual API migration
inside `treepolitics-prod` — Cloud Run, Cloud SQL, Secret Manager,
Artifact Registry. Will does not need to be involved again unless a
budget alert fires.
