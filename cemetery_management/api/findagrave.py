"""
FindAGrave Import Script for Cemetery Management.

Usage:
    bench --site pschurch.v.frappe.cloud execute cemetery_management.api.findagrave.import_memorials
    bench --site pschurch.v.frappe.cloud execute cemetery_management.api.findagrave.import_memorials --kwargs '{"dry_run": true}'
"""

import json
import re
import time

import frappe
import requests
from frappe.utils import cint, now_datetime


FINDAGRAVE_GRAPHQL_URL = "https://www.findagrave.com/orc/graphql"
FINDAGRAVE_SEARCH_URL = "https://www.findagrave.com/cemetery/{cemetery_id}/memorial-search"
FINDAGRAVE_MEMORIAL_URL = "https://www.findagrave.com/memorial/{memorial_id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


@frappe.whitelist()
def enqueue_import(cemetery_name="Pleasant Springs Cemetery"):
    """Enqueue the import as a background job (callable from browser)."""
    frappe.enqueue(
        "cemetery_management.api.findagrave.import_memorials",
        queue="long",
        timeout=3600,
        cemetery_name=cemetery_name,
        dry_run=False,
    )
    frappe.msgprint("FindAGrave import has been queued. Check Background Jobs for progress.")
    return "Import queued"


@frappe.whitelist()
def enqueue_enrich():
    """Enqueue enrichment of all burial records with FindAGrave detail pages."""
    frappe.enqueue(
        "cemetery_management.api.findagrave.enrich_all_records",
        queue="long",
        timeout=7200,
    )
    frappe.msgprint("Enrichment job queued. This will update names, dates, and photos from FindAGrave.")
    return "Enrichment queued"


def enrich_all_records():
    """Fetch detail pages for all burial records that have a FindAGrave memorial ID."""
    records = frappe.get_all(
        "Burial Record",
        filters={"findagrave_memorial_id": ["is", "set"]},
        fields=["name", "findagrave_memorial_id", "first_name", "date_of_birth"],
        order_by="name asc",
        limit_page_length=0,
    )

    total = len(records)
    updated = 0
    errors = 0

    frappe.publish_realtime("msgprint", f"Starting enrichment of {total} records...")

    for idx, rec in enumerate(records, 1):
        memorial_id = rec.findagrave_memorial_id

        try:
            detail = fetch_memorial_details(memorial_id)
            if not detail:
                continue

            doc = frappe.get_doc("Burial Record", rec.name)
            changed = False

            # Update name if currently Unknown
            if doc.first_name == "Unknown" and detail.get("first_name"):
                doc.first_name = detail["first_name"]
                doc.middle_name = detail.get("middle_name", "")
                doc.last_name = detail.get("last_name", "") or "Unknown"
                doc.maiden_name = detail.get("maiden_name", "")
                changed = True

            # Update dates if missing
            if not doc.date_of_birth and detail.get("birth_date_raw"):
                parsed = parse_date_string(detail["birth_date_raw"])
                if parsed:
                    doc.date_of_birth = parsed
                    changed = True

            if not doc.date_of_death and detail.get("death_date_raw"):
                parsed = parse_date_string(detail["death_date_raw"])
                if parsed:
                    doc.date_of_death = parsed
                    changed = True

            # Update veteran info
            if not doc.is_veteran and detail.get("is_veteran"):
                doc.is_veteran = 1
                doc.military_branch = detail.get("military_branch", "")
                changed = True

            # Update bio
            if not doc.findagrave_bio and detail.get("bio"):
                doc.findagrave_bio = detail["bio"]
                changed = True

            if changed:
                doc.flags.ignore_mandatory = True
                doc.save(ignore_permissions=True)
                updated += 1

            if idx % 25 == 0:
                frappe.db.commit()
                frappe.publish_realtime(
                    "msgprint",
                    f"Enrichment progress: {idx}/{total} (updated: {updated})"
                )

        except Exception as e:
            errors += 1
            frappe.log_error(f"Enrich error for {rec.name}: {e}", "FindAGrave Enrich")

        time.sleep(1.5)  # Rate limit

    frappe.db.commit()
    frappe.publish_realtime(
        "msgprint",
        f"Enrichment complete! Updated: {updated}, Errors: {errors}, Total: {total}"
    )


@frappe.whitelist()
def import_memorials(cemetery_name="Pleasant Springs Cemetery", dry_run=False):
    """Main entry point: import all FindAGrave memorials for a cemetery.

    Args:
        cemetery_name: Name of the Cemetery record in Frappe
        dry_run: If True, only fetch and print data without creating records
    """
    frappe.flags.mute_emails = True

    if not frappe.db.exists("Cemetery", cemetery_name):
        frappe.throw(f"Cemetery '{cemetery_name}' not found. Run install first.")

    cemetery = frappe.get_doc("Cemetery", cemetery_name)
    cemetery_id = cemetery.findagrave_id or "17250"

    print(f"\n{'='*60}")
    print(f"FindAGrave Import: {cemetery_name} (ID: {cemetery_id})")
    print(f"Dry Run: {dry_run}")
    print(f"{'='*60}\n")

    # Try scraping approach (more reliable than GraphQL which may require auth)
    memorials = fetch_all_memorials_scrape(cemetery_id)

    if not memorials:
        print("No memorials found. Trying alternative approach...")
        memorials = fetch_all_memorials_search_page(cemetery_id)

    if not memorials:
        print("ERROR: Could not fetch memorials from FindAGrave.")
        return

    print(f"\nTotal memorials fetched: {len(memorials)}")

    created = 0
    skipped = 0
    errors = 0

    for idx, memorial in enumerate(memorials, 1):
        memorial_id = str(memorial.get("memorial_id", ""))

        if not memorial_id:
            continue

        # Check for existing record
        existing = frappe.db.exists(
            "Burial Record",
            {"findagrave_memorial_id": memorial_id}
        )
        if existing:
            skipped += 1
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(memorials)} (created: {created}, skipped: {skipped})")
            continue

        if dry_run:
            print(f"  [DRY RUN] Would create: {memorial.get('first_name', '')} {memorial.get('last_name', '')} (ID: {memorial_id})")
            created += 1
            continue

        try:
            doc = create_burial_record(memorial, cemetery_name)
            created += 1
            if idx % 10 == 0:
                print(f"  Progress: {idx}/{len(memorials)} (created: {created}, skipped: {skipped})")
                frappe.db.commit()
        except Exception as e:
            errors += 1
            print(f"  ERROR creating record for memorial {memorial_id}: {e}")

    frappe.db.commit()

    # Update Cemetery Settings
    if not dry_run:
        settings = frappe.get_single("Cemetery Settings")
        settings.last_findagrave_import = now_datetime()
        settings.import_count = cint(settings.import_count) + created
        settings.save(ignore_permissions=True)
        frappe.db.commit()

    print(f"\n{'='*60}")
    print(f"Import Complete!")
    print(f"  Created: {created}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")


def fetch_all_memorials_scrape(cemetery_id):
    """Fetch all memorials by scraping individual search result pages."""
    all_memorials = []
    page = 1

    while True:
        print(f"  Fetching page {page}...")
        url = f"https://www.findagrave.com/cemetery/{cemetery_id}/memorial-search?page={page}"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"  HTTP {resp.status_code} on page {page}, stopping.")
                break

            html = resp.text
            memorials = parse_search_page(html)

            if not memorials:
                print(f"  No memorials on page {page}, stopping.")
                break

            all_memorials.extend(memorials)
            print(f"  Found {len(memorials)} memorials on page {page} (total: {len(all_memorials)})")

            # Check if there's a next page
            if 'rel="next"' not in html and f"page={page + 1}" not in html:
                break

            page += 1
            time.sleep(1.5)  # Rate limiting

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

    return all_memorials


def parse_search_page(html):
    """Parse a FindAGrave search results page to extract memorial data."""
    memorials = []

    # Find memorial links pattern: /memorial/{id}/{name}
    memorial_pattern = re.compile(
        r'/memorial/(\d+)/([^"\'<>\s]+)',
        re.IGNORECASE
    )

    # Find all memorial IDs
    seen_ids = set()
    for match in memorial_pattern.finditer(html):
        memorial_id = match.group(1)
        if memorial_id in seen_ids:
            continue
        seen_ids.add(memorial_id)

        memorial = {"memorial_id": memorial_id}
        memorials.append(memorial)

    return memorials


def fetch_memorial_details(memorial_id):
    """Fetch detailed information for a single memorial."""
    url = f"https://www.findagrave.com/memorial/{memorial_id}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        html = resp.text
        return parse_memorial_page(html, memorial_id)

    except Exception as e:
        print(f"  Error fetching memorial {memorial_id}: {e}")
        return None


def parse_memorial_page(html, memorial_id):
    """Parse a single FindAGrave memorial page."""
    data = {
        "memorial_id": str(memorial_id),
        "findagrave_url": f"https://www.findagrave.com/memorial/{memorial_id}",
    }

    # Extract name from page title or heading
    # Pattern: <h1 id="bio-name">First Middle Last</h1>
    name_match = re.search(
        r'id="bio-name"[^>]*>([^<]+)</h',
        html, re.IGNORECASE
    )
    if name_match:
        full_name = name_match.group(1).strip()
        parse_name(full_name, data)

    # Extract birth date
    birth_match = re.search(
        r'id="birthDateLabel"[^>]*>[^<]*</span>\s*<time[^>]*datetime="([^"]*)"',
        html, re.IGNORECASE | re.DOTALL
    )
    if not birth_match:
        birth_match = re.search(
            r'Birth[^<]*<[^>]*>(\d{1,2}\s+\w+\s+\d{4}|\d{4})',
            html, re.IGNORECASE
        )
    if birth_match:
        data["birth_date_raw"] = birth_match.group(1).strip()

    # Extract death date
    death_match = re.search(
        r'id="deathDateLabel"[^>]*>[^<]*</span>\s*<time[^>]*datetime="([^"]*)"',
        html, re.IGNORECASE | re.DOTALL
    )
    if not death_match:
        death_match = re.search(
            r'Death[^<]*<[^>]*>(\d{1,2}\s+\w+\s+\d{4}|\d{4})',
            html, re.IGNORECASE
        )
    if death_match:
        data["death_date_raw"] = death_match.group(1).strip()

    # Extract veteran status
    if re.search(r'veteran|military|armed\s+forces', html, re.IGNORECASE):
        vet_match = re.search(
            r'(?:veteran|served\s+in)[^<]*(?:United States\s+)?(Army|Navy|Marine Corps|Air Force|Coast Guard)',
            html, re.IGNORECASE
        )
        if vet_match:
            data["is_veteran"] = True
            data["military_branch"] = vet_match.group(1).title()

    # Extract plot info
    plot_match = re.search(
        r'Plot[:\s]*([^<\n]+)',
        html, re.IGNORECASE
    )
    if plot_match:
        data["plot_info"] = plot_match.group(1).strip()

    # Extract GPS coordinates from embedded data
    lat_match = re.search(r'"latitude":\s*([-\d.]+)', html)
    lng_match = re.search(r'"longitude":\s*([-\d.]+)', html)
    if lat_match and lng_match:
        data["latitude"] = float(lat_match.group(1))
        data["longitude"] = float(lng_match.group(1))

    # Extract primary photo URL
    photo_match = re.search(
        r'"(https://images\.findagrave\.com/photos[^"]+)"',
        html
    )
    if photo_match:
        data["photo_url"] = photo_match.group(1)

    # Extract bio/inscription
    bio_match = re.search(
        r'id="annotationBody"[^>]*>([\s\S]*?)</div>',
        html, re.IGNORECASE
    )
    if bio_match:
        bio_text = re.sub(r'<[^>]+>', '', bio_match.group(1)).strip()
        if bio_text:
            data["bio"] = bio_text[:5000]  # Limit length

    return data


def parse_name(full_name, data):
    """Parse a full name string into first, middle, last, and maiden name."""
    # Handle maiden name in parentheses: "Jane (Smith) Doe"
    maiden_match = re.search(r'\(([^)]+)\)', full_name)
    if maiden_match:
        data["maiden_name"] = maiden_match.group(1).strip()
        full_name = re.sub(r'\([^)]+\)', '', full_name).strip()

    # Handle quotes for nicknames: remove them
    full_name = re.sub(r'"[^"]*"', '', full_name).strip()

    parts = full_name.split()
    if len(parts) >= 3:
        data["first_name"] = parts[0]
        data["last_name"] = parts[-1]
        data["middle_name"] = " ".join(parts[1:-1])
    elif len(parts) == 2:
        data["first_name"] = parts[0]
        data["last_name"] = parts[1]
    elif len(parts) == 1:
        data["first_name"] = parts[0]
        data["last_name"] = ""


def parse_date_string(date_str):
    """Parse various date formats from FindAGrave into a date string.

    Handles: "2020-01-15", "15 Jan 2020", "Jan 2020", "2020", "1 Jan 2020"
    Returns: "YYYY-MM-DD" or None for partial dates
    """
    import datetime

    if not date_str:
        return None

    date_str = date_str.strip()

    # ISO format: 2020-01-15
    iso_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_str)
    if iso_match:
        return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"

    # Full date: 15 Jan 2020 or Jan 15, 2020
    months = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }

    # "15 Jan 2020" or "1 Jan 2020"
    dmy_match = re.match(r'(\d{1,2})\s+(\w{3,})\s+(\d{4})', date_str)
    if dmy_match:
        day = dmy_match.group(1).zfill(2)
        month_str = dmy_match.group(2)[:3].lower()
        year = dmy_match.group(3)
        month = months.get(month_str)
        if month:
            return f"{year}-{month}-{day}"

    # "Jan 15, 2020"
    mdy_match = re.match(r'(\w{3,})\s+(\d{1,2}),?\s+(\d{4})', date_str)
    if mdy_match:
        month_str = mdy_match.group(1)[:3].lower()
        day = mdy_match.group(2).zfill(2)
        year = mdy_match.group(3)
        month = months.get(month_str)
        if month:
            return f"{year}-{month}-{day}"

    # Year only: "2020"
    year_match = re.match(r'^(\d{4})$', date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"  # Default to Jan 1

    return None


def fetch_all_memorials_search_page(cemetery_id):
    """Alternative: Fetch memorial IDs from search, then detail pages."""
    print("  Using individual memorial page scraping (slower but more detailed)...")

    # First get all memorial IDs
    all_ids = []
    page = 1

    while True:
        url = f"https://www.findagrave.com/cemetery/{cemetery_id}/memorial-search?page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                break

            ids = re.findall(r'/memorial/(\d+)/', resp.text)
            unique_ids = list(set(ids) - set(all_ids))

            if not unique_ids:
                break

            all_ids.extend(unique_ids)
            print(f"  Page {page}: found {len(unique_ids)} IDs (total: {len(all_ids)})")
            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

    print(f"\n  Total memorial IDs found: {len(all_ids)}")
    print("  Fetching individual memorial details...")

    memorials = []
    for idx, mid in enumerate(all_ids, 1):
        detail = fetch_memorial_details(mid)
        if detail:
            memorials.append(detail)

        if idx % 20 == 0:
            print(f"  Detail progress: {idx}/{len(all_ids)}")
            frappe.db.commit()

        time.sleep(1.5)  # Rate limiting

    return memorials


def create_burial_record(memorial, cemetery_name):
    """Create a Burial Record from parsed memorial data."""
    memorial_id = str(memorial.get("memorial_id", ""))

    # If we only have a memorial ID (from search page), fetch details
    if not memorial.get("first_name") and memorial_id:
        detail = fetch_memorial_details(memorial_id)
        if detail:
            memorial.update(detail)
        time.sleep(1)  # Rate limit

    first_name = memorial.get("first_name", "").strip() or "Unknown"
    last_name = memorial.get("last_name", "").strip() or "Unknown"

    doc = frappe.new_doc("Burial Record")
    doc.naming_series = "BUR-.YYYY.-.#####"
    doc.first_name = first_name
    doc.middle_name = memorial.get("middle_name", "").strip()
    doc.last_name = last_name
    doc.maiden_name = memorial.get("maiden_name", "").strip()
    doc.cemetery = cemetery_name

    # Parse dates
    birth_date = parse_date_string(memorial.get("birth_date_raw", ""))
    death_date = parse_date_string(memorial.get("death_date_raw", ""))
    if birth_date:
        doc.date_of_birth = birth_date
    if death_date:
        doc.date_of_death = death_date

    # Veteran info
    if memorial.get("is_veteran"):
        doc.is_veteran = 1
        doc.military_branch = memorial.get("military_branch", "")

    # FindAGrave reference
    doc.findagrave_memorial_id = memorial_id
    doc.findagrave_url = memorial.get(
        "findagrave_url",
        f"https://www.findagrave.com/memorial/{memorial_id}"
    )
    doc.findagrave_bio = memorial.get("bio", "")

    # Plot info in notes if available
    plot_info = memorial.get("plot_info", "")
    if plot_info:
        doc.notes = f"FindAGrave Plot Info: {plot_info}"

    # Create a burial plot if GPS data is available
    lat = memorial.get("latitude")
    lng = memorial.get("longitude")
    if lat and lng:
        plot = create_or_get_burial_plot(
            cemetery_name, memorial_id, lat, lng, plot_info
        )
        if plot:
            doc.burial_plot = plot

    # Try to match church member
    church_member = match_church_member(first_name, last_name, death_date)
    if church_member:
        doc.church_member = church_member
        doc.is_church_member = 1

    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)

    return doc


def create_or_get_burial_plot(cemetery_name, memorial_id, lat, lng, plot_info=""):
    """Create a Burial Plot record from GPS data."""
    # Check if a plot with similar coordinates already exists
    existing = frappe.db.get_value(
        "Burial Plot",
        {"cemetery": cemetery_name, "latitude": lat, "longitude": lng},
        "name"
    )
    if existing:
        return existing

    try:
        plot = frappe.new_doc("Burial Plot")
        plot.cemetery = cemetery_name
        plot.plot_number = f"FG-{memorial_id}"
        plot.plot_type = "Standard"
        plot.status = "Occupied"
        plot.max_interments = 1
        plot.current_interments = 1
        plot.latitude = lat
        plot.longitude = lng

        # Try to parse plot_info for section/row
        if plot_info:
            parts = plot_info.split(",")
            if len(parts) >= 2:
                plot.section = parts[0].strip()
                plot.row = parts[1].strip()
            elif len(parts) == 1:
                plot.section = parts[0].strip()

            plot.notes = f"Imported from FindAGrave. Original plot info: {plot_info}"

        plot.flags.ignore_mandatory = True
        plot.insert(ignore_permissions=True)
        return plot.name

    except Exception as e:
        print(f"  Warning: Could not create plot for memorial {memorial_id}: {e}")
        return None


def match_church_member(first_name, last_name, death_date=None):
    """Try to find a matching Church Member record."""
    if not first_name or not last_name:
        return None

    filters = {
        "is_deceased": 1,
        "last_name": last_name,
    }

    # Try exact first name match
    members = frappe.get_all(
        "Church Member",
        filters={**filters, "first_name": first_name},
        fields=["name"],
        limit=1,
    )

    if members:
        return members[0].name

    # Try partial first name match
    members = frappe.get_all(
        "Church Member",
        filters=filters,
        or_filters=[
            ["first_name", "like", f"{first_name}%"],
        ],
        fields=["name"],
        limit=1,
    )

    if members:
        return members[0].name

    return None
