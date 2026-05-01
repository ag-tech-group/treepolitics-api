# Treepolitics — GCP Setup Resume Point

**Last updated:** 2026-05-01
**Status:** Phase 3b blocked. ~5–10 minutes of Will's time required to unblock everything else.

If you are picking up the GCP migration mid-flight (e.g. on a different machine,
new session, weeks later), **read this first.** The full procedural reference
lives in `gcp-setup.md`; the original meeting checklist lives in
`gcp-setup-walkthrough.md`. This doc is the bookmark.

---

## Where we are

### Done ✅

| Phase | Outcome |
|---|---|
| 0 | Will created Spaceship account |
| 1 | `treepolitics.net` push-transferred from Amr to Will on Spaceship |
| 2 | Cloud Identity Free tenant exists on `treepolitics.net`. Domain verified via TXT record. `admin@treepolitics.net` has recovery email + 2FA enrolled. |
| 3a | Billing account `Treepolitics — Main` created with company card |
| 4 (partial) | Will granted himself `roles/resourcemanager.organizationAdmin` and `roles/orgpolicy.policyAdmin` |

### Blocked ❌

| Phase | What | Why |
|---|---|---|
| 3b | Granting Amr `Billing Account User` | DRS enforcing — see root cause below |
| 3c | Budget alert | Not yet attempted |
| 4 | Granting Amr the four org-level IAM roles | Same DRS block |
| 5 | Creating `treepolitics-prod` project | Phase 4 must complete first |

### Root cause

`iam.allowedPolicyMemberDomains` (Domain Restricted Sharing) is enforcing
`allowedValues: [<treepolitics.net customer ID>]`, which is Google's
secure-by-default state for new Cloud Identity orgs. It blocks every IAM grant
to external principals (including Amr's `amr@agtechgroup.solutions`).

The Org Policies UI **accepts** a "Override → Replace → Allow all" save and
renders the policy as "Inactive," but a v1/v2 org-policy API mismatch means
the enforcement engine still reads the original allow-list. Verified by
running `gcloud org-policies describe iam.allowedPolicyMemberDomains
--organization=$ORG_ID` and seeing `allowedValues` still populated despite
the UI claim.

**Do not waste time fighting the UI.** Apply the policy via gcloud v2 YAML —
that's the only path that actually persists.

---

## Resume — Cloud Shell paste-block

**Who:** Will (needs the IAM roles he granted himself in Phase 4 partial).
**Time:** 5 minutes.
**Prereq:** Will signed in to <https://console.cloud.google.com> as
`admin@treepolitics.net`.

Steps:

1. Open **Cloud Shell** — the `>_` icon in the top-right of the GCP console.
2. Paste the entire block below.
3. Confirm each command's output before continuing — they're written to be
   safe to re-run.

```bash
# Auto-fetch the org and billing IDs (no need to memorize)
ORG_ID=$(gcloud organizations list --format="value(ID)" | head -1)
BILLING_ID=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" | head -1)

echo "Org ID:    $ORG_ID"
echo "Billing:   $BILLING_ID"

# Step 1 — Disable DRS via gcloud v2 YAML (UI route is broken)
cat > /tmp/drs-allow-all.yaml <<EOF
name: organizations/${ORG_ID}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - allowAll: true
EOF
gcloud org-policies set-policy /tmp/drs-allow-all.yaml

# Step 2 — Verify (output should show "allowAll: true", no allowedValues block)
gcloud org-policies describe iam.allowedPolicyMemberDomains \
  --organization=$ORG_ID

# Step 3 — Grant Amr Billing Account User
gcloud billing accounts add-iam-policy-binding $BILLING_ID \
  --member="user:amr@agtechgroup.solutions" \
  --role="roles/billing.user"

# Step 4 — Grant Amr the four org-level IAM roles in one loop
for role in \
  roles/resourcemanager.organizationAdmin \
  roles/resourcemanager.projectCreator \
  roles/iam.organizationRoleAdmin \
  roles/resourcemanager.folderAdmin
do
  gcloud organizations add-iam-policy-binding $ORG_ID \
    --member="user:amr@agtechgroup.solutions" \
    --role="$role"
done

echo "Done. Amr is now unblocked. Will can sign out."
```

If Step 1 fails with "permission denied" on `orgpolicy.policy.set`, Will
hasn't actually been granted `roles/orgpolicy.policyAdmin` despite the
intention. Have him re-grant himself that role on the org via the IAM page,
then retry.

If Step 2's output still shows `allowedValues` instead of `allowAll: true`,
something's even weirder — capture the full output and investigate before
proceeding.

---

## Next steps after the paste-block (Amr-driven, no Will needed)

### Phase 3c — Budget alert

`Billing → Budgets & alerts → Create budget`:

- Name: `Treepolitics monthly — alert only`
- Amount: $100/month (alert threshold, not a cap)
- Recipients (under Actions → Manage notifications): Will's recovery email
  AND `amr@agtechgroup.solutions`. Don't rely on default
  "send to billing admins" — `admin@treepolitics.net` is not a real mailbox.

### Phase 5 — Create `treepolitics-prod` project

Now that Amr has Project Creator + Billing Account User:

```bash
gcloud projects create treepolitics-prod \
  --organization=$ORG_ID \
  --name="Treepolitics Prod"

gcloud beta billing projects link treepolitics-prod \
  --billing-account=$BILLING_ID
```

(If `treepolitics-prod` is taken globally, append `-01`.)

### API migration (the actual work)

See `gcp-setup.md` section 7 for the planned services: Cloud Run, Cloud SQL,
Secret Manager, Artifact Registry, Cloud Build / GitHub Actions. None of
that requires further Will involvement.

---

## Hardening pass (recommended within 1 week of resume)

`allowAll: true` on DRS is a deliberate weakening. Restore the guardrail
once Amr is added by switching to an explicit allowlist:

1. Get both customer IDs:
   - `treepolitics.net` — `C0xxxxxxx`. Recoverable from
     `gcloud organizations describe $ORG_ID --format="value(directoryCustomerId)"`.
   - `agtechgroup.solutions` — Amr fetches via his own
     `admin.google.com → Account → Account settings`, or via
     `gcloud organizations list` while authed as
     `amr@agtechgroup.solutions`.

2. Update the policy to allowlist both, replacing the broad allowAll:

   ```bash
   cat > /tmp/drs-allowlist.yaml <<EOF
   name: organizations/${ORG_ID}/policies/iam.allowedPolicyMemberDomains
   spec:
     rules:
     - values:
         allowedValues:
         - C0_TREEPOLITICS_ID_HERE
         - C0_AGTECHGROUP_ID_HERE
   EOF
   gcloud org-policies set-policy /tmp/drs-allowlist.yaml
   ```

3. Verify Amr's existing IAM grants survive the policy tightening — they
   should, because the customer ID is now allowlisted. Test by adding a
   trivial second binding and confirming it succeeds.

---

## Sensitive identifiers

Org ID, customer ID, recovery emails, and billing account ID are NOT in this
repo (it's public). They live in
`/home/amrtg/apps/treepolitics/gcp-infrastructure.md` on the original setup
machine — outside any repo.

**Resuming on a fresh machine?** All those identifiers are reproducible by
signing in to the GCP console as the relevant admin and running:

- `gcloud organizations list` — gives org ID and customer ID
- `gcloud billing accounts list` — gives billing account ID
- `admin.google.com → Account` — confirms the Cloud Identity admin login
  and recovery email

The only non-reproducible bit is Will's chosen recovery email — it's
in his password manager and his Spaceship account; ask him if needed.
