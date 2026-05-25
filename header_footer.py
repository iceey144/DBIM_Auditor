# =========================================================
# DBIM HEADER & FOOTER COMPLIANCE ENGINE
# CLEAN EXPLAINABLE VERSION
# =========================================================

import asyncio
import os
import cv2
import numpy as np

from PIL import Image

from playwright.async_api import async_playwright

from docx import Document
from docx.shared import Inches

# =========================================================
# FOLDERS
# =========================================================

FOLDERS = [

    "screenshots",
    "annotated",
    "reports"

]

for folder in FOLDERS:

    os.makedirs(folder, exist_ok=True)

# =========================================================
# SAFE SCREENSHOT
# =========================================================

async def safe_screenshot(

    page,
    path,
    clip=None

):

    try:

        if clip:

            await page.screenshot(

                path=path,
                clip=clip

            )

        else:

            await page.screenshot(

                path=path,
                full_page=True

            )

        return True

    except:

        return False

# =========================================================
# SAFE IMAGE READ
# =========================================================

def safe_read(path):

    try:

        return cv2.imread(path)

    except:

        return None

# =========================================================
# CONTRAST SCORE
# =========================================================

def calculate_contrast(path):

    img = safe_read(path)

    if img is None:
        return 0

    gray = cv2.cvtColor(

        img,
        cv2.COLOR_BGR2GRAY

    )

    mn = np.min(gray)
    mx = np.max(gray)

    score = round(

        (mx + 0.05)
        /
        (mn + 0.05),

        2

    )

    return score

# =========================================================
# PROPORTION VALIDATION
# =========================================================

def validate_proportion(

    iw,
    ih,
    rw,
    rh

):

    if ih == 0 or rh == 0:
        return False

    ir = iw / ih
    rr = rw / rh

    diff = abs(ir - rr)

    return diff <= 0.35

# =========================================================
# DETECTION BOXES
# =========================================================

def draw_detection_boxes(

    image_path,
    detections,
    output

):

    img = cv2.imread(image_path)

    if img is None:
        return

    for d in detections:

        x = int(d["x"])
        y = int(d["y"])

        w = int(d["w"])
        h = int(d["h"])

        compliant = d["compliant"]

        label = d["label"]

        color = (

            (0,220,0)

            if compliant

            else (0,0,255)

        )

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

            0.7,

            color,

            2

        )

    cv2.imwrite(output, img)

# =========================================================
# ORG NAME
# =========================================================

async def detect_org_name(page):

    try:

        title = await page.title()

        keywords = [

            "ministry",
            "department",
            "government",
            "directorate",
            "mission",
            "scheme"

        ]

        found = []

        for k in keywords:

            if k in title.lower():

                found.append(k)

        return {

            "title": title,
            "found": found

        }

    except:

        return {

            "title": "",
            "found": []

        }

# =========================================================
# EXTRACT BRANDING
# =========================================================

async def extract_branding(page):

    elements = []

    selectors = [

        "header img",
        "nav img",
        "footer img",
        "[class*='logo']",
        "[id*='logo']"

    ]

    idx = 0

    seen = set()

    for selector in selectors:

        try:

            found = await page.query_selector_all(
                selector
            )

            for el in found:

                try:

                    visible = await el.is_visible()

                    if not visible:
                        continue

                    box = await el.bounding_box()

                    if not box:
                        continue

                    if box["width"] < 40:
                        continue

                    if box["height"] < 15:
                        continue

                    key = (

                        f"{round(box['x'])}_"
                        f"{round(box['y'])}"

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    clip = {

                        "x": max(0, box["x"] - 10),
                        "y": max(0, box["y"] - 10),

                        "width": box["width"] + 20,
                        "height": box["height"] + 20

                    }

                    path = (

                        f"screenshots/logo_{idx}.png"
                    )

                    ok = await safe_screenshot(

                        page,
                        path,
                        clip

                    )

                    if not ok:
                        continue

                    try:

                        img = Image.open(path)

                        iw, ih = img.size

                    except:

                        iw = box["width"]
                        ih = box["height"]

                    element_type = (

                        "HEADER"

                        if "header" in selector
                        or "nav" in selector

                        else "FOOTER"

                    )

                    elements.append({

                        "path": path,

                        "type": element_type,

                        "selector": selector,

                        "iw": iw,
                        "ih": ih,

                        "rw": box["width"],
                        "rh": box["height"],

                        "x": box["x"],
                        "y": box["y"],

                        "w": box["width"],
                        "h": box["height"]

                    })

                    print(

                        f"\nBRANDING {idx} DETECTED"
                    )

                    idx += 1

                except:
                    pass

        except:
            pass

    return elements

# =========================================================
# DOCX REPORT
# =========================================================

def generate_docx(report):

    doc = Document()

    doc.add_heading(

        "DBIM Header & Footer Compliance Report",

        level=1

    )

    for item in report:

        doc.add_heading(

            item["title"],

            level=2

        )

        p = doc.add_paragraph()

        p.add_run(

            f"Status: {item['status']}\n\n"

        ).bold = True

        p.add_run(

            item["reason"]

        )

        try:

            doc.add_picture(

                item["image"],

                width=Inches(6)

            )

        except:
            pass

        doc.add_page_break()

    output = (

        "reports/header_footer_report.docx"
    )

    doc.save(output)

    print("\nDOCX REPORT GENERATED")
    print(output)

# =========================================================
# MAIN ENGINE
# =========================================================

async def engine():

    url = input(

        "\nEnter Website URL: "
    )

    report = []

    detections = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(

            headless=False

        )

        page = await browser.new_page(

            viewport={

                "width":1440,
                "height":900

            }

        )

        print("\nOPENING WEBSITE...")

        await page.goto(

            url,
            wait_until="domcontentloaded"

        )

        await page.wait_for_timeout(5000)

        full_page = (

            "screenshots/full_page.png"
        )

        await safe_screenshot(

            page,
            full_page

        )

        # =================================================
        # RULE 21
        # =================================================

        org = await detect_org_name(page)

        if len(org["found"]) > 0:

            status = "COMPLIANT"

            reason = f"""
RULE 21: PASSED

Detected website title:
{org['title']}

Detected organization keywords:
{', '.join(org['found'])}

Reason:
The website title clearly
indicates an official government
organization structure.
"""

        else:

            status = "NON-COMPLIANT"

            reason = f"""
RULE 21: FAILED

Detected website title:
{org['title']}

Reason:
No recognizable government
organization naming pattern
was detected in the title.
"""

        report.append({

            "title":
            "Rule 21 - Website Naming",

            "status":
            status,

            "reason":
            reason,

            "image":
            full_page

        })

        # =================================================
        # BRANDING
        # =================================================

        branding = await extract_branding(page)

        for idx, logo in enumerate(branding):

            compliant = True

            reasons = []

            # =============================================
            # LOCATION
            # =============================================

            location = (

                "top header region"

                if logo["y"] < 250

                else "footer region"

            )

            # =============================================
            # RULE 20
            # =============================================

            intrinsic_ratio = round(

                logo["iw"] / logo["ih"],

                2

            )

            rendered_ratio = round(

                logo["rw"] / logo["rh"],

                2

            )

            valid = validate_proportion(

                logo["iw"],
                logo["ih"],

                logo["rw"],
                logo["rh"]

            )

            if rendered_ratio > intrinsic_ratio:

                distortion = (

                    "horizontally stretched"

                )

            else:

                distortion = (

                    "vertically compressed"

                )

            if not valid:

                compliant = False

                reasons.append(

                    f"""
RULE 20: FAILED

Intrinsic aspect ratio:
{intrinsic_ratio}

Rendered aspect ratio:
{rendered_ratio}

Reason:
The branding element appears
{distortion}, which changes the
original logo/emblem proportions.
"""
                )

            else:

                reasons.append(

                    f"""
RULE 20: PASSED

Intrinsic aspect ratio:
{intrinsic_ratio}

Rendered aspect ratio:
{rendered_ratio}

Reason:
The branding element preserves
its original proportions correctly.
"""
                )

            # =============================================
            # RULE 22
            # =============================================

            contrast_score = calculate_contrast(

                logo["path"]

            )

            contrast_ok = contrast_score >= 2

            if not contrast_ok:

                compliant = False

                reasons.append(

                    f"""
RULE 22: FAILED

Detected contrast ratio:
{contrast_score}

Reason:
The branding element blends
poorly with the background,
reducing visibility.
"""
                )

            else:

                reasons.append(

                    f"""
RULE 22: PASSED

Detected contrast ratio:
{contrast_score}

Reason:
The branding element remains
clearly visible against the
background.
"""
                )

            # =============================================
            # RULE 19
            # =============================================

            reasons.append(

                """
RULE 19: PARTIALLY VERIFIABLE

Reason:
Automated systems cannot fully
verify whether the emblem/logo
originates from an officially
authorized government source.
"""
            )

            # =============================================
            # RULE 23
            # =============================================

            reasons.append(

                """
RULE 23: PARTIALLY VERIFIABLE

Reason:
Full DBIM structural conformity
requires manual verification of
header/footer layout standards.
"""
            )

            reason = "\n".join(reasons)

            reason += f"""

Detected location:
{location}

Detected selector:
{logo['selector']}

Rendered dimensions:
{int(logo['rw'])} x {int(logo['rh'])}
"""

            status = (

                "COMPLIANT"

                if compliant

                else "NON-COMPLIANT"

            )

            detections.append({

                "x": logo["x"],
                "y": logo["y"],

                "w": logo["w"],
                "h": logo["h"],

                "label":

                    f"{logo['type']} | {status}",

                "compliant": compliant

            })

            report.append({

                "title":

                f"{logo['type']} Branding Element {idx}",

                "status":
                status,

                "reason":
                reason,

                "image":
                logo["path"]

            })

        # =================================================
        # DETECTION OVERVIEW
        # =================================================

        annotated = (

            "annotated/detected_boxes.png"
        )

        draw_detection_boxes(

            full_page,
            detections,
            annotated

        )

        report.insert(

            0,

            {

                "title":
                "Detected Branding Regions",

                "status":
                "VISUAL EVIDENCE",

                "reason":

                "Detected branding elements "
                "highlighted with compliance "
                "status boxes.",

                "image":
                annotated

            }

        )

        # =================================================
        # DOCX
        # =================================================

        generate_docx(report)

        await browser.close()

# =========================================================
# RUN
# =========================================================

asyncio.run(
    engine()
)