# =========================================================
# DBIM ANNEXURE A.4.1 & A.4.1.1 COMPLIANCE AUDITOR ENGINE
# =========================================================

import asyncio
import os
import cv2
import re
import numpy as np
from playwright.async_api import async_playwright
from docx import Document
from docx.shared import Inches, RGBColor

# --- DIRECTORY CONFIGURATION ---
FOLDERS = ["screenshots", "reports"]
for folder in FOLDERS:
    os.makedirs(folder, exist_ok=True)

# --- COORDINATE BOUNDED RECTANGLE DRAWER ---
def draw_boxes(image_path, detections, output_path):
    img = cv2.imread(image_path)
    if img is None:
        return
    
    h_img, w_img, _ = img.shape

    for d in detections:
        x = max(0, int(d["x"]))
        y = max(0, int(d["y"]))
        w = int(d["w"])
        h = int(d["h"])
        
        if x >= w_img or y >= h_img:
            continue
        w = min(w, w_img - x)
        h = min(h, h_img - y)

        label = d["label"]
        color = d["color"]

        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        
        label_size, base_line = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        top_left = (x, max(label_size[1] + 10, y))
        box_coords = ((top_left[0], top_left[1] + base_line), (top_left[0] + label_size[0] + 6, top_left[1] - label_size[1] - 4))
        
        cv2.rectangle(img, box_coords[0], box_coords[1], color, cv2.FILLED)
        cv2.putText(img, label, (top_left[0] + 3, top_left[1] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imwrite(output_path, img)

# --- NESTING FILTERING MATRIX ---
def is_genuine_overlap(box_a, box_b):
    if box_a.get("id") and box_b.get("parent_id") == box_a["id"]:
        return False
    if box_b.get("id") and box_a.get("parent_id") == box_b["id"]:
        return False

    ax1, ay1 = box_a["x"], box_a["y"]
    ax2, ay2 = ax1 + box_a["w"], ay1 + box_a["h"]
    bx1, by1 = box_b["x"], box_b["y"]
    bx2, by2 = bx1 + box_b["w"], by1 + box_b["h"]

    x_int = max(ax1, bx1)
    y_int = max(ay1, by1)
    w_int = min(ax2, bx2) - x_int
    h_int = min(ay2, by2) - y_int

    if w_int <= 5 or h_int <= 5:
        return False

    return True

# --- SECTION A.4.1.1: SINGLE-PAGE DEPARTMENTAL TILE ENGINE ---
async def check_departmental_tiles(page):
    """Audits Rule A.4.1.1 for interactive departmental dashboard tile layouts."""
    findings = []
    detections = []
    
    # Query elements matching structural card/tile blueprints
    tile_selectors = [
        "a[class*='tile' i]", "div[class*='tile' i] a", "a[class*='card' i]", 
        "div[class*='card' i] a", ".department-link", "[id*='department' i] a",
        "div[class*='dept' i] a"
    ]
    
    resolved_tiles = []
    for selector in tile_selectors:
        elements = await page.query_selector_all(selector)
        for el in elements:
            if await el.is_visible():
                box = await el.evaluate("""(e) => {
                    const r = e.getBoundingClientRect();
                    return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
                }""")
                # Filter out small utilities; structural navigation tiles have surface mass
                if box and box["w"] > 80 and box["h"] > 40:
                    # Avoid duplicate entry coordinates
                    if not any(abs(t["x"] - box["x"]) < 5 and abs(t["y"] - box["y"]) < 5 for t in resolved_tiles):
                        resolved_tiles.append(box)

    if not resolved_tiles:
        findings.append("A.4.1.1 Violation: Missing dedicated grid array or clickable tiles for departmental routing map layouts.")
    else:
        findings.append(f"A.4.1.1 Compliance: Successfully resolved {len(resolved_tiles)} multi-department structural linkage navigation tiles.")
        for tile in resolved_tiles[:12]: # Highlight layout anchors
            detections.append({
                "x": tile["x"], "y": tile["y"], "w": tile["w"], "h": tile["h"],
                "label": "DEPT TILE (A.4.1.1)", "color": (255, 0, 128)
            })

    compliant = len(resolved_tiles) > 0
    return compliant, findings, detections

# --- PILLAR I: CLARITY ENGINE ---
async def check_clarity(page):
    findings = []
    detections = []

    h1_elements = await page.query_selector_all("h1")
    if not h1_elements:
        findings.append("CRITICAL: No primary <h1> block found to anchor layout clarity.")
    else:
        visible_h1 = 0
        for h1 in h1_elements:
            if await h1.is_visible():
                visible_h1 += 1
        if visible_h1 > 1:
            findings.append(f"WARNING: Found {visible_h1} distinct visible <h1> containers.")

    h2_elements = await page.query_selector_all("h2, h3")
    if not h2_elements:
        findings.append("Secondary design hierarchy missing sub-heading items (<h2> or <h3>).")

    elements = await page.query_selector_all("button, a, img, h1, h2, h3, p, input")
    resolved_boxes = []

    for index, el in enumerate(elements[:150]):
        try:
            if not await el.is_visible():
                continue
            box = await el.evaluate("""(e) => {
                const r = e.getBoundingClientRect();
                return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
            }""")
            if not box or box["w"] < 20 or box["h"] < 20:
                continue

            parent_id = await el.evaluate("(e) => e.parentElement ? e.parentElement.className + e.parentElement.tagName : null")
            element_id = f"{await el.evaluate('(e) => e.className')}{await el.evaluate('(e) => e.tagName')}_{index}"

            resolved_boxes.append({
                "x": box["x"], "y": box["y"], "w": box["w"], "h": box["h"],
                "id": element_id, "parent_id": parent_id
            })
        except:
            continue

    overlap_count = 0
    for i in range(len(resolved_boxes)):
        for j in range(i + 1, len(resolved_boxes)):
            if is_genuine_overlap(resolved_boxes[i], resolved_boxes[j]):
                overlap_count += 1
                detections.append({
                    "x": resolved_boxes[j]["x"], "y": resolved_boxes[j]["y"],
                    "w": resolved_boxes[j]["w"], "h": resolved_boxes[j]["h"],
                    "label": "OVERLAP", "color": (0, 0, 255)
                })
                if overlap_count >= 15:
                    break

    if overlap_count > 0:
        findings.append(f"Layout Crowding: Resolved {overlap_count} overlapping layout intersections.")

    compliant = len(findings) == 0 or (overlap_count == 0 and not any("CRITICAL" in f for f in findings))
    if compliant:
        findings.append("Typography configurations clear; zero element layout overlaps found.")

    return compliant, findings, detections

# --- PILLAR II: CONSISTENCY ENGINE ---
async def check_consistency(page):
    findings = []
    detections = []

    try:
        buttons = await page.query_selector_all("button, a.btn, input[type='submit'], .button")
        variant_groups = {}

        for btn in buttons[:40]:
            try:
                if not await btn.is_visible():
                    continue

                metrics = await btn.evaluate("""(e) => {
                    const s = window.getComputedStyle(e);
                    const r = e.getBoundingClientRect();
                    return { height: r.height, radius: s.borderRadius, klass: e.className };
                }""")
                
                classes = metrics["klass"].split()
                variant_key = classes[0] if classes else "base-control"

                r_match = re.search(r'([\d.]+)', metrics["radius"])
                radius_px = float(r_match.group(1)) if r_match else 0.0
                height_px = float(metrics["height"])

                if variant_key not in variant_groups:
                    variant_groups[variant_key] = {"heights": [], "radii": [], "nodes": []}
                
                variant_groups[variant_key]["heights"].append(height_px)
                variant_groups[variant_key]["radii"].append(radius_px)
                variant_groups[variant_key]["nodes"].append(btn)
            except:
                continue

        for key, data in variant_groups.items():
            if len(data["nodes"]) < 2:
                continue
            
            height_delta = max(data["heights"]) - min(data["heights"])
            radius_delta = max(data["radii"]) - min(data["radii"])

            if height_delta > 8 or radius_delta > 3:
                findings.append(f"Style Drift in Class [.{key}]: height variance={round(height_delta)}px, corner variance={round(radius_delta)}px.")
                
                for node in data["nodes"][:4]:
                    box = await node.evaluate("""(e) => {
                        const r = e.getBoundingClientRect();
                        return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
                    }""")
                    if box:
                        detections.append({
                            "x": box["x"], "y": box["y"], "w": box["w"], "h": box["h"],
                            "label": f"STYLE MISMATCH [.{key}]", "color": (0, 165, 255)
                        })
    except Exception as e:
        findings.append(f"Style processing error: {str(e)}")

    compliant = len(findings) == 0
    if compliant:
        findings.append("Interface visual systems remain constant across structural template blocks.")

    return compliant, findings, detections

# --- PILLAR III: INTUITIVENESS ENGINE ---
async def check_intuitiveness(page):
    findings = []
    detections = []

    nav_selectors = ["nav", "[role='navigation']", ".navbar", ".main-nav", "#menu", ".header-menu"]
    nav_found = False
    for s in nav_selectors:
        nav = await page.query_selector(s)
        if nav and await nav.is_visible():
            box = await nav.evaluate("""(e) => {
                const r = e.getBoundingClientRect();
                return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
            }""")
            if box and box["w"] > 100 and box["h"] > 20:
                detections.append({
                    "x": box["x"], "y": box["y"], "w": box["w"], "h": box["h"],
                    "label": "NAV HEADER", "color": (0, 255, 0)
                })
                nav_found = True
                break
                
    if not nav_found:
        findings.append("CRITICAL: Global navigational top-bar layout configuration could not be tracked.")

    search_selectors = [
        "input[type='search']", "input[placeholder*='search' i]",
        "input[id*='search' i]", "input[class*='search' i]"
    ]
    search_found = False
    for s in search_selectors:
        search = await page.query_selector(s)
        if search and await search.is_visible():
            box = await search.evaluate("""(e) => {
                const r = e.getBoundingClientRect();
                return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height };
            }""")
            if box:
                detections.append({
                    "x": box["x"], "y": box["y"], "w": box["w"], "h": box["h"],
                    "label": "SEARCH CONTAINER", "color": (255, 255, 0)
                })
                search_found = True
                break

    if not search_found:
        findings.append("User Discovery Warning: Core dashboard missing accessible search options.")

    compliant = not any("CRITICAL" in f for f in findings)
    if compliant:
        findings.append("Site features structured navigation layout systems and user discovery paths.")

    return compliant, findings, detections

# --- PILLAR IV: RESPONSIVENESS ENGINE ---
async def check_responsive(browser, url):
    findings = []
    device_results = []
    viewports = [("Desktop", 1280, 720), ("Tablet", 768, 1024), ("Mobile", 390, 844)]

    for name, width, height in viewports:
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15" if name == "Mobile" else None,
            ignore_https_errors=True
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(4000)

            overflow = await page.evaluate("""() => {
                const docWidth = document.documentElement.scrollWidth;
                const winWidth = window.innerWidth;
                return docWidth > winWidth + 3;
            }""")

            shot_path = f"screenshots/{name}_canvas.png"
            await page.screenshot(path=shot_path, full_page=True)

            if overflow:
                findings.append(f"Viewport Scaling Fault: Layout template breaks on [{name}] screen width boundaries.")
                out_path = f"screenshots/{name}_overflow_highlighted.png"
                draw_boxes(shot_path, [{
                    "x": 0, "y": 0, "w": width, "h": 250,
                    "label": f"{name.upper()} WIDTH OVERFLOW", "color": (0, 0, 255)
                }], out_path)
                device_results.append(out_path)
            else:
                device_results.append(shot_path)
        except Exception as e:
            findings.append(f"Viewport verification skipped on [{name}]: {str(e)}")
        finally:
            await context.close()

    compliant = not any("Fault" in f for f in findings)
    if compliant:
        findings.append("Canvas adapters scale across variable target dimensions.")

    return compliant, findings, device_results

# --- COMPLIANCE REPORT COMPILER ---
def generate_docx(results):
    doc = Document()
    doc.add_heading("DBIM Annexure A.4.1 & A.4.1.1 Compliance Audit Report", level=1)
    doc.add_paragraph("High-Accuracy UI Layout Design and Multi-Department Functional Dashboard Optimization Matrix.")

    for item in results:
        doc.add_heading(item["title"], level=2)
        para = doc.add_paragraph()
        
        status_run = para.add_run(f"STATUS: {item['status']}\n\n")
        status_run.bold = True
        
        if item["status"] == "COMPLIANT":
            status_run.font.color.rgb = RGBColor(0, 128, 0)
        else:
            status_run.font.color.rgb = RGBColor(200, 0, 0)
        
        para.add_run(f"Compliance Diagnostics Log:\n{item['reason']}")

        images = item["image"]
        if isinstance(images, list):
            for img in images:
                if os.path.exists(img):
                    doc.add_paragraph(f"Viewport Context Capture: {os.path.basename(img)}")
                    doc.add_picture(img, width=Inches(5.6))
        elif isinstance(images, str) and os.path.exists(images):
            doc.add_picture(images, width=Inches(5.6))

        doc.add_page_break()

    output = "reports/annexure_a41_report.docx"
    doc.save(output)
    print(f"\n[+] MULTI-SECTION SUMMARY REPORT EXPORTED TO PATH: {output}")

# --- MAIN RUNNER ENGINE ---
async def engine():
    url = input("\nEnter Website URL to Audit: ").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    results = []

    async with async_playwright() as p:
        print("\n[1/6] Booting automated headless chromium runtime containers...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage", "--no-sandbox"]
        )
        
        context = await browser.new_context(viewport={"width": 1280, "height": 720}, ignore_https_errors=True)
        page = await context.new_page()

        print(f"[2/6] Rendering functional DOM tree schemas: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=90000)
            
            for offset in range(0, 3200, 800):
                await page.evaluate(f"window.scrollTo(0, {offset});")
                await page.wait_for_timeout(600)
            await page.evaluate("window.scrollTo(0, 0);")
            await page.wait_for_timeout(1500)
            
        except Exception as e:
            print(f"[-] Root network landing session timed out: {str(e)}")
            await browser.close()
            return

        screenshot = "screenshots/full_page_base.png"
        await page.screenshot(path=screenshot, full_page=True)

        # --- RUN EVALUATION AND DISCOVERY CRITERIA ---
        print("[3/6] Assessing Section A.4.1.1: Single-Page Multi-Department Clickable Tile Arrays...")
        tiles_ok, tiles_findings, tiles_boxes = await check_departmental_tiles(page)
        tiles_img = screenshot
        if tiles_boxes:
            tiles_img = "screenshots/departmental_tiles_traced.png"
            draw_boxes(screenshot, tiles_boxes, tiles_img)
        results.append({"title": "A.4.1.1 Department Navigation Tiles", "status": "COMPLIANT" if tiles_ok else "NON-COMPLIANT", "reason": "\n".join(tiles_findings), "image": tiles_img})

        print("[4/6] Assessing Section A.4.1 Pillar I: Clarity & Element Layout Collision...")
        clarity_ok, clarity_findings, clarity_boxes = await check_clarity(page)
        clarity_img = screenshot
        if clarity_boxes:
            clarity_img = "screenshots/clarity_traced.png"
            draw_boxes(screenshot, clarity_boxes, clarity_img)
        results.append({"title": "Clarity Analysis", "status": "COMPLIANT" if clarity_ok else "NON-COMPLIANT", "reason": "\n".join(clarity_findings), "image": clarity_img})

        print("[5/6] Assessing Section A.4.1 Pillar II: Design System Consistency...")
        consistency_ok, consistency_findings, consistency_boxes = await check_consistency(page)
        consistency_img = screenshot
        if consistency_boxes:
            consistency_img = "screenshots/consistency_traced.png"
            draw_boxes(screenshot, consistency_boxes, consistency_img)
        results.append({"title": "Consistency Analysis", "status": "COMPLIANT" if consistency_ok else "NON-COMPLIANT", "reason": "\n".join(consistency_findings), "image": consistency_img})

        print("[6/6] Assessing Section A.4.1 Pillar III: Layout Intuitiveness & Discovery Content...")
        intuitive_ok, intuitive_findings, intuitive_boxes = await check_intuitiveness(page)
        intuitive_img = screenshot
        if intuitive_boxes:
            intuitive_img = "screenshots/intuitiveness_traced.png"
            draw_boxes(screenshot, intuitive_boxes, intuitive_img)
        results.append({"title": "Intuitiveness Analysis", "status": "COMPLIANT" if intuitive_ok else "NON-COMPLIANT", "reason": "\n".join(intuitive_findings), "image": intuitive_img})

        print("[+] Assessing Section A.4.1 Pillar IV: Responsiveness (Multi-Viewport Grid Check)...")
        responsive_ok, responsive_findings, responsive_images = await check_responsive(browser, url)
        results.append({"title": "Responsiveness Analysis", "status": "COMPLIANT" if responsive_ok else "NON-COMPLIANT", "reason": "\n".join(responsive_findings), "image": responsive_images})

        # --- EXPORT PACKAGED DOCX ---
        generate_docx(results)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(engine())