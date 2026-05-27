# =========================================================
# DBIM ANNEXURE A.3 AUDITOR
# ULTRA REFINED ACCURACY VERSION
# =========================================================

import asyncio
import os
import re
import cv2

from playwright.async_api import async_playwright
from docx import Document
from docx.shared import Inches

# =========================================================
# FOLDERS
# =========================================================

FOLDERS = [

    "screenshots",
    "reports"

]

for folder in FOLDERS:

    os.makedirs(folder, exist_ok=True)

# =========================================================
# DBIM TAGS
# =========================================================

INFO_TAGS = [

    "policy",
    "policies",

    "news",
    "latest news",

    "event",
    "events",

    "guideline",
    "guidelines",

    "form",
    "forms",

    "scheme",
    "schemes",

    "notification",
    "notifications",

    "circular",
    "circulars"

]

PERSONA_TAGS = [

    "student",
    "students",

    "farmer",
    "farmers",

    "citizen",
    "citizens",

    "business",
    "startup",

    "doctor",
    "patient",

    "women",
    "youth"

]

# =========================================================
# NORMALIZE
# =========================================================

def normalize(text):

    return re.sub(

        r"\s+",
        " ",
        str(text).lower()

    ).strip()

# =========================================================
# SCREENSHOT
# =========================================================

async def take_screenshot(

    page,
    path

):

    await page.screenshot(

        path=path,
        full_page=True

    )

# =========================================================
# VALID BOX
# =========================================================

def valid_box(box):

    if not box:
        return False

    w = box["width"]
    h = box["height"]

    # tiny noise
    if w < 45:
        return False

    if h < 18:
        return False

    # giant sections
    if w > 450:
        return False

    if h > 180:
        return False

    return True

# =========================================================
# DRAW DETECTIONS
# =========================================================

def draw_detection_boxes(

    image_path,
    detections,
    output_path

):

    img = cv2.imread(image_path)

    if img is None:
        return

    for d in detections:

        x = int(d["x"])
        y = int(d["y"])

        w = int(d["w"])
        h = int(d["h"])

        label = d["label"]

        color = d["color"]

        cv2.rectangle(

            img,

            (x,y),
            (x+w,y+h),

            color,
            3

        )

        cv2.putText(

            img,

            label,

            (x,y-10),

            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2

        )

    cv2.imwrite(output_path, img)

# =========================================================
# FILTER ELEMENTS
# =========================================================

async def should_ignore(el, box):

    try:

        if not await el.is_visible():
            return True

        if not valid_box(box):
            return True

        html = await el.evaluate(
            "(e) => e.outerHTML"
        )

        lower_html = normalize(html)

        # footer spam
        if "footer" in lower_html:
            return True

        style = await el.get_attribute("style")

        if style:

            style = normalize(style)

            if "display:none" in style:
                return True

            if "visibility:hidden" in style:
                return True

        return False

    except:
        return True

# =========================================================
# DETECT INFORMATION TAGGING
# =========================================================

async def detect_information_tags(page):

    detections = []

    evidence = []

    seen = set()

    selectors = [

        ".tag",
        ".badge",
        ".chip",
        ".category",
        ".label",

        "[class*='tag']",
        "[class*='badge']",
        "[class*='chip']",
        "[class*='category']",

        ".card",
        ".service-card",

        "button",
        "span",
        "a"

    ]

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    text = await el.inner_text()

                    if not text:
                        continue

                    lower = normalize(text)

                    # avoid paragraphs
                    if len(lower.split()) > 6:
                        continue

                    matched = None

                    for tag in INFO_TAGS:

                        if tag in lower:

                            matched = tag
                            break

                    if not matched:
                        continue

                    box = await el.bounding_box()

                    if await should_ignore(el, box):
                        continue

                    key = (

                        matched,
                        int(box["x"]),
                        int(box["y"])

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    evidence.append({

                        "tag": matched,
                        "text": text.strip()

                    })

                    detections.append({

                        "x": box["x"],
                        "y": box["y"],

                        "w": box["width"],
                        "h": box["height"],

                        "label": matched.upper(),

                        "color": (0,255,0)

                    })

                except:
                    pass

        except:
            pass

    return evidence, detections

# =========================================================
# DETECT PERSONA TAGGING
# =========================================================

async def detect_persona_tags(page):

    detections = []

    evidence = []

    seen = set()

    selectors = [

        "nav a",
        ".card",
        ".service-card",
        ".tile",
        ".user-card",

        "button",
        "a"

    ]

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    text = await el.inner_text()

                    if not text:
                        continue

                    lower = normalize(text)

                    # avoid huge paragraphs
                    if len(lower.split()) > 10:
                        continue

                    matched = None

                    for tag in PERSONA_TAGS:

                        if tag in lower:

                            matched = tag
                            break

                    if not matched:
                        continue

                    box = await el.bounding_box()

                    if await should_ignore(el, box):
                        continue

                    key = (

                        matched,
                        int(box["x"]),
                        int(box["y"])

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    evidence.append({

                        "persona": matched,
                        "text": text.strip()

                    })

                    detections.append({

                        "x": box["x"],
                        "y": box["y"],

                        "w": box["width"],
                        "h": box["height"],

                        "label": matched.upper(),

                        "color": (255,0,0)

                    })

                except:
                    pass

        except:
            pass

    return evidence, detections

# =========================================================
# DETECT SEARCH
# =========================================================

async def detect_search(page):

    detections = []

    evidence = []

    seen = set()

    selectors = [

        "input[type='search']",
        "input[placeholder*='search' i]"

    ]

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    box = await el.bounding_box()

                    if await should_ignore(el, box):
                        continue

                    # realistic header search only
                    if box["y"] > 350:
                        continue

                    if box["width"] < 150:
                        continue

                    placeholder = await el.get_attribute(
                        "placeholder"
                    )

                    key = (

                        int(box["x"]),
                        int(box["y"])

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    evidence.append({

                        "placeholder": placeholder
                    })

                    detections.append({

                        "x": box["x"],
                        "y": box["y"],

                        "w": box["width"],
                        "h": box["height"],

                        "label": "SEARCH",

                        "color": (0,200,255)

                    })

                except:
                    pass

        except:
            pass

    return evidence, detections

# =========================================================
# DETECT BREADCRUMBS
# =========================================================

async def detect_breadcrumbs(page):

    detections = []

    evidence = []

    seen = set()

    selectors = [

        ".breadcrumb",
        "[class*='breadcrumb']",
        "nav[aria-label*='breadcrumb' i]"

    ]

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    text = await el.inner_text()

                    if not text:
                        continue

                    lower = normalize(text)

                    # real breadcrumb structure
                    if ">" not in lower and "/" not in lower:
                        continue

                    if len(lower.split()) > 15:
                        continue

                    box = await el.bounding_box()

                    if await should_ignore(el, box):
                        continue

                    key = (

                        int(box["x"]),
                        int(box["y"])

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    evidence.append({

                        "text": text.strip()

                    })

                    detections.append({

                        "x": box["x"],
                        "y": box["y"],

                        "w": box["width"],
                        "h": box["height"],

                        "label": "BREADCRUMB",

                        "color": (255,120,0)

                    })

                except:
                    pass

        except:
            pass

    return evidence, detections

# =========================================================
# DOCX
# =========================================================

def generate_docx(results):

    doc = Document()

    doc.add_heading(

        "DBIM Annexure A.3 Audit Report",

        level=1

    )

    doc.add_paragraph(

        "Structured CMS tagging and "
        "discoverability compliance audit."

    )

    for item in results:

        doc.add_heading(

            item["title"],
            level=2

        )

        para = doc.add_paragraph()

        para.add_run(

            f"STATUS: {item['status']}\n\n"

        ).bold = True

        para.add_run(item["reason"])

        try:

            doc.add_picture(

                item["image"],
                width=Inches(6)

            )

        except:
            pass

        doc.add_page_break()

    output = "reports/annexure_a3_report.docx"

    doc.save(output)

    print("\nDOCX GENERATED")
    print(output)

# =========================================================
# MAIN ENGINE
# =========================================================

async def engine():

    url = input(
        "\nEnter Website URL: "
    )

    results = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(

            headless=False,

            slow_mo=400,

            args=[

                "--disable-blink-features=AutomationControlled",

                "--disable-dev-shm-usage",

                "--no-sandbox",

                "--disable-gpu"

            ]

        )

        context = await browser.new_context(

            viewport={

                "width":1280,
                "height":720

            },

            ignore_https_errors=True

        )

        page = await context.new_page()

        print("\nOPENING WEBSITE...")

        try:

            await page.goto(

                url,

                wait_until="domcontentloaded",

                timeout=120000

            )

            await page.wait_for_load_state(
                "networkidle"
            )

        except Exception as e:

            print(f"\nLOAD FAILED:\n{e}")

            await browser.close()

            return

        # =================================================
        # HUMAN-LIKE SCROLLING
        # =================================================

        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(2000)

        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(2000)

        await page.mouse.wheel(0, -2500)
        await page.wait_for_timeout(2000)

        print("\nWEBSITE LOADED")

        screenshot = "screenshots/full_page.png"

        await take_screenshot(

            page,
            screenshot

        )

        # =================================================
        # A.3.1 INFORMATION TAGGING
        # =================================================

        print("\nTESTING A.3.1")

        info_evidence, info_boxes = await detect_information_tags(page)

        info_compliant = len(info_evidence) > 0

        info_image = screenshot

        if info_compliant:

            info_image = "screenshots/info_detection.png"

            draw_detection_boxes(

                screenshot,
                info_boxes,
                info_image

            )

            lines = []

            for e in info_evidence[:5]:

                lines.append(

                    f"- Structured tag detected: '{e['text']}'"
                )

            reason = f"""
RULE: Information-Type Tagging

STATUS: COMPLIANT

Reason:
Structured CMS category labels,
chips, badges, or metadata tags
representing information types
were detected.

Evidence:
{chr(10).join(lines)}
"""

        else:

            reason = """
RULE: Information-Type Tagging

STATUS: NON-COMPLIANT

Reason:
No structured CMS category labels,
chips, badges, or metadata tags
representing information types
were detected.
"""

        results.append({

            "title":
            "A.3.1 Information-Type Tagging",

            "status":

            "COMPLIANT"

            if info_compliant

            else "NON-COMPLIANT",

            "reason":
            reason,

            "image":
            info_image

        })

        # =================================================
        # A.3.2 PERSONA TAGGING
        # =================================================

        print("\nTESTING A.3.2")

        persona_evidence, persona_boxes = await detect_persona_tags(page)

        persona_compliant = len(persona_evidence) > 0

        persona_image = screenshot

        if persona_compliant:

            persona_image = "screenshots/persona_detection.png"

            draw_detection_boxes(

                screenshot,
                persona_boxes,
                persona_image

            )

            lines = []

            for e in persona_evidence[:5]:

                lines.append(

                    f"- Persona structure detected: '{e['text']}'"
                )

            reason = f"""
RULE: Persona-Based Tagging

STATUS: COMPLIANT

Reason:
Persona-oriented navigation,
cards, or structured user-group
sections were detected.

Evidence:
{chr(10).join(lines)}
"""

        else:

            reason = """
RULE: Persona-Based Tagging

STATUS: NON-COMPLIANT

Reason:
No persona-oriented navigation,
cards, or structured user-group
sections were detected.
"""

        results.append({

            "title":
            "A.3.2 Persona-Based Tagging",

            "status":

            "COMPLIANT"

            if persona_compliant

            else "NON-COMPLIANT",

            "reason":
            reason,

            "image":
            persona_image

        })

        # =================================================
        # SEARCH
        # =================================================

        print("\nTESTING SEARCH")

        search_evidence, search_boxes = await detect_search(page)

        search_compliant = len(search_evidence) > 0

        search_image = screenshot

        if search_compliant:

            search_image = "screenshots/search_detection.png"

            draw_detection_boxes(

                screenshot,
                search_boxes,
                search_image

            )

            placeholder = search_evidence[0].get(
                "placeholder"
            )

            reason = f"""
RULE: Search Discoverability

STATUS: COMPLIANT

Reason:
Search functionality supporting
content discoverability was
detected.

Evidence:
Search input detected with
placeholder:
'{placeholder}'
"""

        else:

            reason = """
RULE: Search Discoverability

STATUS: NON-COMPLIANT

Reason:
No search functionality supporting
content discoverability was
detected.
"""

        results.append({

            "title":
            "Search Discoverability",

            "status":

            "COMPLIANT"

            if search_compliant

            else "NON-COMPLIANT",

            "reason":
            reason,

            "image":
            search_image

        })

        # =================================================
        # BREADCRUMBS
        # =================================================

        print("\nTESTING BREADCRUMBS")

        breadcrumb_evidence, breadcrumb_boxes = await detect_breadcrumbs(page)

        breadcrumb_compliant = len(breadcrumb_evidence) > 0

        breadcrumb_image = screenshot

        if breadcrumb_compliant:

            breadcrumb_image = "screenshots/breadcrumb_detection.png"

            draw_detection_boxes(

                screenshot,
                breadcrumb_boxes,
                breadcrumb_image

            )

            lines = []

            for e in breadcrumb_evidence[:3]:

                lines.append(

                    f"- Breadcrumb detected: '{e['text']}'"
                )

            reason = f"""
RULE: Breadcrumb Navigation

STATUS: COMPLIANT

Reason:
Breadcrumb navigation structures
supporting content hierarchy were
detected.

Evidence:
{chr(10).join(lines)}
"""

        else:

            reason = """
RULE: Breadcrumb Navigation

STATUS: NON-COMPLIANT

Reason:
No breadcrumb navigation
structures were detected.
"""

        results.append({

            "title":
            "Breadcrumb Navigation",

            "status":

            "COMPLIANT"

            if breadcrumb_compliant

            else "NON-COMPLIANT",

            "reason":
            reason,

            "image":
            breadcrumb_image

        })

        # =================================================
        # GENERATE DOCX
        # =================================================

        generate_docx(results)

        await browser.close()

# =========================================================
# RUN
# =========================================================

asyncio.run(
    engine()
)