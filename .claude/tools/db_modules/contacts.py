"""Contact CRUD operations."""

import json
import sys

from db_modules.client import sb
from db_modules.helpers import _ensure_company, _resolve_job_prefix, _upsert_contact, _link_contact_job


def batch_add_contacts(args):
    """Batch add/update contacts from JSON on stdin.

    Expected JSON format (array of contact objects):
    [
      {
        "name": "Rebecca Tang",
        "title": "PM, Google",
        "linkedin_url": "linkedin.com/in/rebeccatang",
        "company": "Google",
        "relationship_type": "referral",
        "outreach_status": "draft_ready",
        "priority": "high",
        "is_personal_connection": true,
        "outreach_message_md": "Subject: ...\\n\\nHey Rebecca...",
        "mutual_connection_notes": "...",
        "notes": "...",
        "jobs": ["4cfb2cb8", "1c1682a7"]
      }
    ]

    Fields:
      name                  (required) Full name
      company               (required) Company name — looked up or auto-created
      title                 Current role title
      linkedin_url          Used as dedup key — updates if already exists
      relationship_type     recruiter | hiring_manager | referral | alumni | unknown
      outreach_status       identified | draft_ready | sent | connected | responded |
                            meeting_scheduled | warm
      priority              high | medium | low
      is_personal_connection  true/false
      outreach_message_md   Full outreach draft (include Subject: line at top)
      mutual_connection_notes  Notes on shared network
      notes                 General notes
      jobs                  Array of job ID prefixes (first 8 chars) to link
    """
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No JSON provided on stdin")
        sys.exit(1)

    try:
        contacts_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(contacts_data, list):
        contacts_data = [contacts_data]  # accept single object too

    ok_insert, ok_update, fail = 0, 0, 0

    for item in contacts_data:
        name = item.get("name")
        company_name = item.get("company")
        if not name or not company_name:
            print(f"⚠️  Skipping entry missing name or company: {item.get('name', '?')}")
            fail += 1
            continue

        # Resolve company
        company_id = _ensure_company(company_name)
        if not company_id:
            print(f"  ❌ Could not resolve company '{company_name}' for {name}")
            fail += 1
            continue

        # Build contact payload (exclude agent-side keys)
        contact_payload = {
            "company_id": company_id,
            "name": name,
        }
        for field in ("title", "linkedin_url", "relationship_type", "outreach_status",
                      "priority", "is_personal_connection", "outreach_message_md",
                      "mutual_connection_notes", "notes"):
            if field in item:
                contact_payload[field] = item[field]

        contact_id, action = _upsert_contact(contact_payload)
        if not contact_id:
            print(f"  ❌ Failed: {name}")
            fail += 1
            continue

        marker = "✅" if action == "inserted" else "↺ "
        print(f"  {marker} {action.capitalize()}: {name}")

        # Resolve and link jobs
        for prefix in (item.get("jobs") or []):
            job_id, job_title = _resolve_job_prefix(str(prefix))
            if job_id:
                _link_contact_job(contact_id, job_id)
            else:
                print(f"    ⚠️  Job prefix '{prefix}' not found — skipping link")

        if action == "inserted":
            ok_insert += 1
        else:
            ok_update += 1

    total = len(contacts_data)
    print(f"\n✅ batch-add-contacts: {ok_insert} inserted, {ok_update} updated, {fail} failed (of {total} total)")
    print("  Run sync_contacts.py to regenerate the memory file.")


def find_contact(args):
    """Search for contacts by name, company, or LinkedIn URL. Returns JSON."""
    query = sb.table("contacts").select(
        "id, name, title, linkedin_url, outreach_status, priority, notes, "
        "company:companies(name)"
    )

    if args.name:
        query = query.ilike("name", f"%{args.name}%")
    if args.company:
        company_res = sb.table("companies").select("id").ilike("name", f"%{args.company}%").execute()
        if company_res.data:
            company_ids = [c["id"] for c in company_res.data]
            query = query.in_("company_id", company_ids)
        else:
            print("[]")
            return
    if args.linkedin_url:
        query = query.ilike("linkedin_url", f"%{args.linkedin_url}%")

    res = query.limit(args.limit).execute()
    import json
    print(json.dumps(res.data, indent=2, default=str))


def update_contact(args):
    """Update a contact's outreach status or notes by LinkedIn URL or ID."""
    # Find the contact
    if args.linkedin_url:
        res = sb.table("contacts").select("id, name").eq("linkedin_url", args.linkedin_url).execute()
    elif args.id:
        res = sb.table("contacts").select("id, name").eq("id", args.id).execute()
    else:
        print("ERROR: Provide --linkedin-url or --id")
        sys.exit(1)

    if not res.data:
        print("❌ Contact not found")
        sys.exit(1)

    contact_id = res.data[0]["id"]
    contact_name = res.data[0]["name"]

    data = {}
    if args.status:
        data["outreach_status"] = args.status
    if args.notes:
        data["notes"] = args.notes
    if args.message:
        data["outreach_message_md"] = args.message
    if args.last_contacted:
        data["last_contacted_at"] = args.last_contacted

    if not data:
        print("Nothing to update. Provide --status, --notes, --message, or --last-contacted.")
        return

    sb.table("contacts").update(data).eq("id", contact_id).execute()
    print(f"✅ Updated {contact_name}: {data}")
    print("  Run sync_contacts.py to regenerate the memory file.")
