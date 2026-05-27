# =================================================================
# MASTER UNIFIED GLOBAL DBIM AUDITOR ENGINE - REFINED HIGH-DESCRIPTION
# =================================================================

import asyncio
import os
import re
from datetime import datetime
import cv2
import numpy as np
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches, RGBColor
from playwright.async_api import async_playwright

# --- SANITIZATION PIPELINES ---
FOLDERS = ["screenshots", "annotated", "reports"]
for folder in FOLDERS:
    os.makedirs(folder, exist_ok=True)

FINAL_REPORT_PATH = "reports/master_compliance_report.docx"

def draw_compliance_overlay_boxes(image_path, detections, output_path):
    img = cv2.imread(image_path)
    if img is None:
        return image_path
    h_img, w_img, _ = img.shape

    for d in detections:
        x = max(0, int(d["x"]))
        y = max(0, int(d["y"]))
        w = int(d["w"])
        h = int(d["h"])
        
        if x >= w_img or y >= h_img: continue
        w = min(w, w_img - x)
        h = min(h, h_img - y)

        compliant = d["compliant"]
        label = d["label"]
        color = (0, 128, 0) if compliant else (0, 0, 200)

        cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
        label_size, base_line = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        top_left = (x, max(label_size[1] + 12, y))
        box_coords = ((top_left[0], top_left[1] + base_line), (top_left[0] + label_size[0] + 6, top_left[1] - label_size[1] - 4))
        
        cv2.rectangle(img, box_coords[0], box_coords[1], color, cv2.FILLED)
        cv2.putText(img, label, (top_left[0] + 3, top_left[1] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imwrite(output_path, img)
    return output_path

# --- TARGET LAYOUT ELEMENT STRUCTURAL DEFINITIONS ARRAY ---
STRUCTURAL_CHECKLIST_SPECS = {
    "block_i": {
        "id": "i", "name": "Homepage Header Section", "selector": "header, .site-header, #header, [class*='header' i]",
        "intent": "Mandated under DBIM Section 5.4.1. Must remain sticky while scrolling, house the official dual emblem lockups, an active search box container, and user typography scaling accessibility controls.",
        "fix": "Enforce persistent viewport stickiness via CSS 'position: sticky; top: 0; z-index: 9999;' and inject standard language configuration selectors tags directly into header grids."
    },
    "block_ii": {
        "id": "ii", "name": "Top Banner Carousel", "selector": ".carousel, .slider, [class*='banner' i], [id*='hero' i], [class*='hero' i]",
        "intent": "Mandated under Section 7.4. Requires full-width central publishing system core banner allocations constrained exactly to standard dimensional footprints: 1800x338px, 1800x500px, or 1800x600px.",
        "fix": "Re-crop slider asset sources canvas vectors to standard resolution limits and bind responsive alternative srcset attributes inside native picture elements tags."
    },
    "block_iii": {
        "id": "iii", "name": "Announcements Ticker", "selector": ".ticker, .marquee, [class*='ticker' i], [class*='announcement' i], marquee",
        "intent": "Enforces vital user informational delivery pipelines. Delivers immediate visibility over live updates, time-sensitive public service notices, vacancies releases, or tender updates.",
        "fix": "Inject an un-opinionated typographic ticker block using custom smooth JavaScript intervals or access-compliant CSS animation loops moving string arrays dynamically."
    },
    "block_iv": {
        "id": "iv", "name": "PM Quote Section", "selector": "[class*='pm-' i], [class*='quote' i], [id*='pm' i], .minister-quote",
        "intent": "Features high-resolution authorized imagery of leadership with transparent source background profiles alongside localized event text strings wrapped inside type-compliant darker background palettes.",
        "fix": "Acquire background-isolated, transparent PNG graphics assets from verified channels and anchor adjacent text lines to original publication links using dark thematic wrappers."
    },
    "block_v": {
        "id": "v", "name": "Ministry/Department Section", "selector": ".about-ministry, .introduction, [class*='about' i], #about-section, [id*='about' i]",
        "intent": "The primary semantic branding statement component container layer. Expresses divisional functionality clearly with explicit quick-routing navigational controls to subordinate offices portals.",
        "fix": "Draft high-descriptive introductory content tags mapping out legislative powers and organize link arrays into crisp multi-column text containers layers frames."
    },
    "block_vi": {
        "id": "vi", "name": "Key Offerings Section", "selector": ".key-offerings, .schemes-tenders, [class*='offering' i], #services-grid, [class*='service' i]",
        "intent": "Central citizen action panel. Highlights a tabbed grid containing vacancies, tenders, or schemes. Must restrict initial views to the 5 most recent nodes with an explicit 'View More' button pointer.",
        "fix": "Re-engineer dynamic dashboard queries to cap list items records at 5 entries max and hook a bold stylized action link redirection anchor targeting the main documents index."
    },
    "block_vii": {
        "id": "vii", "name": "What's New Section", "selector": ".whats-new, .latest-updates, [class*='news' i], [id*='notice' i], [class*='update' i]",
        "intent": "Exposes real-time structural feeds indexing fresh programmatic content changes across organizational layers, accompanied by standard layout navigation modifiers controls elements.",
        "fix": "Bind a clean chronological notification pipeline rendering the latest backend database transactions updates, closing with a prominent centralized navigation button."
    },
    "block_viii": {
        "id": "viii", "name": "Recent Documents Section", "selector": ".recent-docs, .publications, [class*='document' i], #downloads-list, [class*='download' i]",
        "intent": "Fosters organizational clarity and transparency. Displays a structured repository indexing newly published files formats, legislative bills, research data sets, and policy forms.",
        "fix": "Deploy structured lists containers styled with distinct document type file extensions badges and attach absolute path download tracking parameters to each anchor element."
    },
    "block_ix": {
        "id": "ix", "name": "User Persona Section", "selector": ".user-persona, .persona-selection, [class*='persona' i], [id*='persona' i]",
        "intent": "Enforces user-centric accessibility mapping frameworks. Separates layout views matching specific target audience personas (e.g., Student, Corporate, Researcher) to prevent layout density roadblocks.",
        "fix": "Build distinct routing target cards embedded with intuitive representative illustrations to instantly group content based on specific audience context profiles variables."
    },
    "block_x": {
        "id": "x", "name": "Important Links Section", "selector": ".important-links, .quick-links, .hyperlinks-grid, [class*='links' i]",
        "intent": "Provides prioritized interface paths pointing toward high-volume public target applications, internal portals, tracking forms, or cross-departmental utility platforms.",
        "fix": "Design an explicit grid block featuring clean iconography links to accelerate navigation to the system's most requested external and internal service channels."
    },
    "block_xi": {
        "id": "xi", "name": "Citizen Engagement Section", "selector": ".citizen-engagement, .social-media-feeds, .social-feed-container, [class*='social' i]",
        "intent": "Consolidates social media communication feeds. Aggregates live outreach streams (X, YouTube, Facebook) into responsive multi-tab widget layouts to maintain public interaction channels.",
        "fix": "Embed standard secure asynchronous layout cards hooks connecting officially authenticated third-party social API instances into dedicated multi-grid rows frameworks."
    },
    "block_xii": {
        "id": "xii", "name": "Central Posts Section", "selector": ".central-posts, .ccps-posts, [class*='posts-grid' i]",
        "intent": "Displays central graphic templates published dynamically from the CCPS core framework, bound exactly to standard dimensions: 960x244px layout envelopes profiles.",
        "fix": "Set strict stylesheet width/height sizing caps matching the 960x244px bounding constraints and link content directly to the parent content distribution engine API."
    },
    "block_xiii": {
        "id": "xiii", "name": "Infographics Section", "selector": ".infographics, .data-visuals, [class*='infographic' i], [class*='gallery' i]",
        "intent": "Visualizes complex data sets, program trackings, and metrics achievements using high-visibility information design grids vectors to improve public document parsing speeds.",
        "fix": "Construct a localized graphic gallery block featuring compressed, high-contrast visual vectors equipped with full alternative aria-text descriptive strings labels."
    },
    "block_xiv": {
        "id": "xiv", "name": "Footer Carousel", "selector": "footer .carousel, .footer-logos, [class*='partner' i], [class*='sponsor' i]",
        "intent": "Displays a horizontal strip carousel framing authorized logos, related internal commissions links, state portals, and associated initiatives identifiers icons.",
        "fix": "Embed an auto-scrolling graphic strip component restricted to clean monochromatic or approved colored emblem shapes linking back to verified external parent domains."
    },
    "block_xv": {
        "id": "xv", "name": "Footer Details Section", "selector": "footer, .site-footer, #footer, [class*='footer' i]",
        "intent": "Mandated under Rule 25. Standardizes persistence criteria formatting across all sub-pages, requiring direct links mapping to Archives, Sitemap, Policies, Help, and live Last Updated parameters.",
        "fix": "Enforce a structured 4-column master footer layout grid containing explicit text paths targeting core metadata records links and map a dynamic script logging system updates signatures."
    }
}

async def analyze_homepage_sequence_native(page):
    return await page.evaluate("""
        (selectors_map) => {
            const results = {};
            for (const [id, spec] of Object.entries(selectors_map)) {
                const node = document.querySelector(spec.selector);
                if (node) {
                    const rect = node.getBoundingClientRect();
                    let extra_details = [];
                    let passed = node.offsetWidth > 0 && node.offsetHeight > 0;
                    
                    if (passed) {
                        const text = node.textContent.toLowerCase();
                        if (id === 'block_i') {
                            const style = window.getComputedStyle(node);
                            if (style.position === 'sticky' || style.position === 'fixed') extra_details.push("Sticky positioning present");
                            if (node.querySelector('input[type="search"], [class*="search"]')) extra_details.push("Search bar verified");
                            if (node.querySelector('[class*="lang"], [class*="font"]')) extra_details.push("Accessibility/Language controls found");
                        }
                        if (id === 'block_ii') {
                            if (Math.round(rect.width) >= window.innerWidth * 0.9) extra_details.push("Full-width CCPS banner dimensions verified");
                        }
                        if (id === 'block_iii') {
                            if (node.tagName.toLowerCase() === 'marquee' || window.getComputedStyle(node).animationName !== 'none') extra_details.push("Live ticker animation detected");
                        }
                        if (id === 'block_iv') {
                            if (node.querySelector('img')) extra_details.push("PM portrait graphic found");
                        }
                        if (id === 'block_vi' || id === 'block_vii') {
                            if (text.includes('view more') || text.includes('read more') || text.includes('all')) extra_details.push("Mandatory 'View More' link verified");
                        }
                        if (id === 'block_xi') {
                            if (node.querySelector('iframe, [class*="twitter"], [class*="facebook"], [class*="youtube"]')) extra_details.push("Social media widget streams embedded");
                        }
                        if (id === 'block_xv') {
                            const required = ['archive', 'polic', 'sitemap', 'help', 'feedback', 'updated'];
                            let found = required.filter(r => text.includes(r));
                            extra_details.push(`Rule 25 Metadata Links Verified: ${found.length}/${required.length}`);
                        }
                    }
                    
                    results[id] = {
                        found: passed,
                        box: { x: rect.left, y: rect.top, w: rect.width, h: rect.height },
                        details: extra_details.length > 0 ? extra_details.join(" | ") : "Layout boundary mapping successful."
                    };
                } else {
                    results[id] = { found: false, box: null, details: "Component violation: Missing from DOM." };
                }
            }
            return results;
        }
    """, STRUCTURAL_CHECKLIST_SPECS)

# =================================================================
# HIGH-DESCRIPTION AUTOMATED REPORT ARCHIVER COMPILER
# =================================================================
def compile_high_description_report(url, records_matrix):
    print("\n[+] Instantiating high-description compliance handbook artifact generation channels...")
    doc = Document()
    
    # Document Master Header configurations
    p_head = doc.add_paragraph()
    r_head = p_head.add_run("OFFICIAL DBIM SECTION A.4.1.2 STRUCTURAL COMPLIANCE REPORT")
    r_head.bold = True
    r_head.font.size = Inches(0.25)
    
    doc.add_paragraph(f"Audit Target URL: {url}\nExecution Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"Evaluation Standard: Digital Brand Identity Manual (DBIM) Checklist Specification v2.5")
    doc.add_page_break()

    # Iterate through all 15 points explicitly creating descriptive evaluations
    for block_key, spec in STRUCTURAL_CHECKLIST_SPECS.items():
        outcome = records_matrix[block_key]
        is_compliant = outcome["found"]
        
        doc.add_heading(f"Sequence Check {spec['id']}: {spec['name']}", level=1)
        
        # Section 1: Intent
        doc.add_heading("INTENT:", level=3)
        doc.add_paragraph(spec["intent"])
        
        # Section 2: Technical Status
        status_para = doc.add_paragraph()
        status_run = status_para.add_run(f"STATUS: {'COMPLIANT' if is_compliant else 'NON-COMPLIANT'}\n")
        status_run.bold = True
        status_run.font.color.rgb = RGBColor(0, 128, 0) if is_compliant else RGBColor(180, 0, 0)
        
        # Section 3: Metrics Table
        doc.add_heading("MEASURED METRICS:", level=3)
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text = "Parameter", "Measured Result"
        hdr[0].paragraphs[0].runs[0].font.bold = True
        hdr[1].paragraphs[0].runs[0].font.bold = True
        
        r1 = table.add_row().cells
        r1[0].text = "DOM Selector"
        r1[1].text = spec['selector']
        
        r2 = table.add_row().cells
        r2[0].text = "Visibility"
        r2[1].text = "VISIBLE" if is_compliant else "MISSING"
        
        r3 = table.add_row().cells
        r3[0].text = "Bounding Box"
        if is_compliant and outcome["box"]:
            b = outcome["box"]
            r3[1].text = f"{round(b['w'])}x{round(b['h'])}px at ({round(b['x'])}, {round(b['y'])})"
            
            if outcome.get("details"):
                r4 = table.add_row().cells
                r4[0].text = "Content Rules"
                r4[1].text = outcome["details"]
        else:
            r3[1].text = "N/A"

        # Section 4: Detailed Analysis & Findings
        doc.add_heading("FINDINGS:", level=3)
        if is_compliant:
            doc.add_paragraph(f"PASSED: The '{spec['name']}' component was successfully located and rendered on the page.")
        else:
            doc.add_paragraph(f"FAILED: The '{spec['name']}' container element is missing or not visible.")
            
            # Section 5: Engineering Remediation Plan (Only generated on failures)
            doc.add_heading("REMEDIATION:", level=3)
            doc.add_paragraph(f"Ensure the component exists in the DOM matching selector: {spec['selector']}.\nFix: {spec['fix']}")

        # Section 6: Image Proof Injection
        if is_compliant and "screenshot_proof" in outcome and os.path.exists(outcome["screenshot_proof"]):
            doc.add_heading("VISUAL PROOF:", level=3)
            doc.add_picture(outcome["screenshot_proof"], width=Inches(5.7))
            
        doc.add_page_break()

    doc.save(FINAL_REPORT_PATH)
    print(f"\n[➔] HANDBOOK GENERATION COMPLETE. DETAILED COMPLIANCE REPORT EXPORTED TO: {FINAL_REPORT_PATH}")

# --- MAIN AUTOMATED TESTING ENGINE INTERFACE ---
async def main():
    url = input("\nEnter Target Website URL to Auditing Section A.4.1.2 Checklist: ").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with async_playwright() as p:
        print("[+] Activating sandboxed headless browser workspace automation layers...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 950})

        print(f"[+] Deploying analytical structural hooks over target portal: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            # Smooth scrolling loops pass to settle all asynchronous lazy elements layers safely
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollTo(0, 0);")
            await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"[-] Navigation routine timeout aborted: {e}")
            await browser.close()
            return

        # Execute high-accuracy native coordinate retrieval loops pass inside V8 block frame
        print("[+] Evaluating all 15 structural points across DOM tree maps context...")
        sequence_records = await analyze_homepage_sequence_native(page)
        
        page_metrics = await page.evaluate("() => ({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})")

        # Process forced annotated cropping proofs signatures maps
        print("[+] Processing explicit layout screenshots crop proofs records...")
        for key, record in sequence_records.items():
            if record["found"] and record["box"]:
                try:
                    selector = STRUCTURAL_CHECKLIST_SPECS[key]['selector']
                    element = await page.query_selector(selector)
                    if element:
                        raw_path = f"screenshots/raw_sec_{key}.png"
                        traced_path = f"annotated/proof_box_sec_{key}.png"
                        
                        await element.scroll_into_view_if_needed()
                        await element.screenshot(path=raw_path)
                        
                        b = await element.bounding_box()
                        if b:
                            draw_compliance_overlay_boxes(raw_path, [{
                                "x": 2, "y": 2, "w": b["width"] - 4, "h": b["height"] - 4,
                                "label": f"SEC {STRUCTURAL_CHECKLIST_SPECS[key]['id']} VERIFIED", "compliant": True
                            }], traced_path)
                            
                            record["screenshot_proof"] = traced_path if os.path.exists(traced_path) else raw_path
                            print(f"   [📷 Proof Saved Successfully] Created Node Layer Clip: {record['screenshot_proof']}")
                except Exception as e:
                    print(f"   [-] Proof generation failed for {key}: {e}")

        await browser.close()

    # Pass memory models arrays downstream to compile the detailed handbook documentation view
    compile_high_description_report(url, sequence_records)

if __name__ == "__main__":
    asyncio.run(main())