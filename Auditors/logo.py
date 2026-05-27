# =========================================================
# ADVANCED DBIM LOGO AUDITOR - VS CODE VERSION
# =========================================================

import asyncio
import os
import cv2
import numpy as np
import requests
from docx import Document
from docx.shared import Inches
from io import BytesIO
from PIL import Image

from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

# =========================================================
# FOLDERS
# =========================================================

FOLDERS = [

    "logos",
    "expected_logos",
    "comparison",
    "reports",
    "temp"

]

for folder in FOLDERS:

    os.makedirs(folder, exist_ok=True)

# =========================================================
# DBIM RULES
# =========================================================

VALID_FORMATS = [

    "png",
    "jpg",
    "jpeg",
    "svg",
    "webp"

]

MAX_SIZE_KB = 100

# =========================================================
# DOWNLOAD IMAGE
# =========================================================

def download_image(url, path):

    try:

        headers = {

            "User-Agent":

            "Mozilla/5.0"

        }

        r = requests.get(

            url,
            timeout=20,
            headers=headers

        )

        if r.status_code != 200:
            return False

        with open(path, "wb") as f:

            f.write(r.content)

        return True

    except:
        return False

# =========================================================
# SAFE IMAGE LOAD
# =========================================================

def safe_read(path):

    try:

        if not os.path.exists(path):
            return None

        img = cv2.imread(path)

        return img

    except:
        return None

# =========================================================
# FILE SIZE
# =========================================================

def get_file_size_kb(path):

    try:

        size = os.path.getsize(path)

        return round(size / 1024, 2)

    except:
        return 0

# =========================================================
# EXTENSION
# =========================================================

def get_extension(url):

    parsed = urlparse(url).path

    ext = parsed.split(".")[-1].lower()

    if ext in VALID_FORMATS:
        return ext

    return "unknown"

# =========================================================
# LOGO DETECTION HEURISTIC
# =========================================================

async def is_probable_logo(el):

    try:

        tag = await el.evaluate(

            "e => e.tagName.toLowerCase()"

        )

        attrs = await el.evaluate(

            """
            e => ({

                alt:e.alt || "",
                id:e.id || "",
                class:e.className || "",
                aria:e.getAttribute('aria-label') || ""

            })
            """

        )

        text = (

            attrs["alt"]
            +
            attrs["id"]
            +
            attrs["class"]
            +
            attrs["aria"]

        ).lower()

        keywords = [

            "logo",
            "brand",
            "navbar-brand",
            "site-logo"

        ]

        for k in keywords:

            if k in text:
                return True

        if tag == "svg":
            return True

        box = await el.bounding_box()

        if not box:
            return False

        if box["width"] < 40:
            return False

        if box["height"] < 15:
            return False

        return True

    except:
        return False

# =========================================================
# EXPECTED DBIM LOGO
# =========================================================

def generate_expected_logo(

    asset_path,
    rendered_width,
    rendered_height

):

    ext = asset_path.split(".")[-1].lower()

    # ============================================
    # SVG HANDLING
    # ============================================

    if ext == "svg":

        # use displayed rendered screenshot
        # because PIL cannot open SVG

        fallback = asset_path.replace(

            "temp",
            "logos"

        )

        if os.path.exists(fallback):

            img = Image.open(

                fallback

            ).convert("RGBA")

        else:

            return np.ones(

                (180,360,3),

                dtype=np.uint8

            ) * 255

    # ============================================
    # NORMAL IMAGE
    # ============================================

    else:

        img = Image.open(

            asset_path

        ).convert("RGBA")

    alpha = img.split()[-1]

    bbox = alpha.getbbox()

    if bbox:

        img = img.crop(bbox)

    ow, oh = img.size

    # ============================================
    # PRESERVE ASPECT RATIO
    # ============================================

    scale = min(

        300 / ow,
        120 / oh

    )

    nw = int(ow * scale)
    nh = int(oh * scale)

    resized = img.resize(

        (nw, nh),

        Image.LANCZOS

    )

    canvas = Image.new(

        "RGBA",

        (360,180),

        (255,255,255,0)

    )

    x = (360 - nw)//2
    y = (180 - nh)//2

    canvas.paste(

        resized,
        (x,y),
        resized

    )

    return cv2.cvtColor(

        np.array(canvas),

        cv2.COLOR_RGBA2BGR

    )

# =========================================================
# DISTORTION
# =========================================================

def validate_proportion(

    intrinsic_w,
    intrinsic_h,
    rendered_w,
    rendered_h

):

    if intrinsic_h == 0:
        return False

    if rendered_h == 0:
        return False

    intrinsic_ratio = intrinsic_w / intrinsic_h

    rendered_ratio = rendered_w / rendered_h

    diff = abs(

        intrinsic_ratio
        -
        rendered_ratio

    )

    return diff <= 0.15

# =========================================================
# CONTRAST
# =========================================================

def validate_contrast(path):

    img = safe_read(path)

    if img is None:
        return False

    gray = cv2.cvtColor(

        img,
        cv2.COLOR_BGR2GRAY

    )

    mn = np.min(gray)
    mx = np.max(gray)

    contrast = (

        (mx+0.05)
        /
        (mn+0.05)

    )

    return contrast >= 2

# =========================================================
# CREATE PANEL
# =========================================================

def create_panel(

    current,
    expected,
    output,
    compliant

):

    img1 = safe_read(current)

    if img1 is None:
        return

    img2 = expected

    img1 = cv2.resize(

        img1,
        (450,220)

    )

    img2 = cv2.resize(

        img2,
        (450,220)

    )

    canvas = np.ones(

        (330,950,3),

        dtype=np.uint8

    ) * 255

    canvas[
        60:280,
        20:470
    ] = img1

    canvas[
        60:280,
        480:930
    ] = img2

    cv2.putText(

        canvas,

        "CURRENT WEBSITE LOGO",

        (80,35),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        (0,0,255),

        2

    )

    cv2.putText(

        canvas,

        "EXPECTED DBIM LOGO",

        (540,35),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        (0,150,0),

        2

    )

    status = (

        "COMPLIANT"

        if compliant

        else "NON-COMPLIANT"

    )

    color = (

        (0,150,0)

        if compliant

        else (0,0,255)

    )

    cv2.putText(

        canvas,

        status,

        (350,315),

        cv2.FONT_HERSHEY_SIMPLEX,

        1,

        color,

        3

    )

    cv2.imwrite(output, canvas)

# =========================================================
# EXTRACT LOGOS
# =========================================================

async def extract_logos(page, base_url):

    selectors = [

        "img",
        "svg",
        "[style*='background']",
        ".logo",
        "[class*='logo']",
        "[id*='logo']",
        "header img",
        "footer img",
        "picture source"

    ]

    logos = []

    seen = set()

    idx = 0

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    probable = await is_probable_logo(el)

                    if not probable:
                        continue

                    box = await el.bounding_box()

                    if not box:
                        continue

                    rendered_w = box["width"]
                    rendered_h = box["height"]

                    if rendered_w < 40:
                        continue

                    if rendered_h < 15:
                        continue

                    tag = await el.evaluate(

                        "e => e.tagName.toLowerCase()"

                    )

                    asset_url = None

                    # ====================================
                    # IMG
                    # ====================================

                    if tag == "img":

                        asset_url = await el.get_attribute(
                            "src"
                        )

                    # ====================================
                    # SOURCE
                    # ====================================

                    elif tag == "source":

                        asset_url = await el.get_attribute(
                            "srcset"
                        )

                    # ====================================
                    # CSS BG
                    # ====================================

                    else:

                        bg = await el.evaluate(

                            """
                            e => getComputedStyle(e)
                            .backgroundImage
                            """

                        )

                        if "url(" in bg:

                            asset_url = bg.split("url(")[1]
                            asset_url = asset_url.split(")")[0]

                            asset_url = asset_url.replace(
                                "'",
                                ""
                            )

                            asset_url = asset_url.replace(
                                '"',
                                ""
                            )

                    if not asset_url:

                        display = f"logos/logo_{idx}.png"

                        try:

                            await el.screenshot(
                                path=display
                            )

                        except:
                            continue

                        asset = display

                    else:

                        asset_url = urljoin(

                            base_url,
                            asset_url

                        )

                        if asset_url in seen:
                            continue

                        seen.add(asset_url)

                        ext = get_extension(
                            asset_url
                        )

                        asset = (

                            f"temp/logo_{idx}.{ext}"
                        )

                        success = download_image(

                            asset_url,
                            asset

                        )

                        if not success:
                            continue

                        display = (

                            f"logos/logo_{idx}.png"
                        )

                        try:

                            await el.screenshot(
                                path=display
                            )

                        except:
                            continue

                    # ====================================
                    # INTRINSIC SIZE
                    # ====================================

                    try:

                        pil = Image.open(asset)

                        intrinsic_w, intrinsic_h = pil.size

                    except:

                        intrinsic_w = rendered_w
                        intrinsic_h = rendered_h

                    logos.append({

                        "display": display,

                        "asset": asset,

                        "rendered_w": rendered_w,
                        "rendered_h": rendered_h,

                        "intrinsic_w": intrinsic_w,
                        "intrinsic_h": intrinsic_h,

                        "format": get_extension(asset),

                        "file_size":

                            get_file_size_kb(asset)

                    })

                    print(

                        f"\nLOGO {idx} EXTRACTED"
                    )

                    idx += 1

                except Exception as e:

                    print(str(e))

        except Exception as e:

            print(str(e))

    return logos
# =========================================================
# GENERATE DOCX REPORT
# =========================================================

def generate_docx(report):

    doc = Document()

    doc.add_heading(

        "DBIM Logo Compliance Report",

        level=1

    )

    doc.add_paragraph(

        "Automated DBIM logo auditing "
        "report generated using the "
        "AI-powered compliance engine."

    )

    for item in report:

        doc.add_heading(

            f"Logo {item['logo']}",

            level=2

        )

        p = doc.add_paragraph()

        p.add_run(

            f"Status: {item['status']}\n"

        ).bold = True

        p.add_run(

            item["reason"]

        )

        comparison = item["comparison"]

        if os.path.exists(comparison):

            try:

                doc.add_picture(

                    comparison,

                    width=Inches(6)

                )

            except:
                pass

        doc.add_page_break()

    output = (

        "reports/logo_report.docx"

    )

    doc.save(output)

    print(

        "\nDOCX REPORT GENERATED:"
    )

    print(output)

# =========================================================
# MAIN ENGINE
# =========================================================

async def logo_engine():

    url = input(

        "\nEnter Website URL: "

    )

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

        print("\nEXTRACTING LOGOS...")

        logos = await extract_logos(

            page,
            url

        )

        print(

            f"\nTOTAL LOGOS: {len(logos)}"
        )

        report = []

        # =================================================
        # ANALYSIS
        # =================================================

        for idx, logo in enumerate(logos):

            compliant = True

            explanations = []

            # =============================================
            # FORMAT
            # =============================================

            if logo["format"] not in VALID_FORMATS:

                compliant = False

                explanations.append(

                    f"""
FORMAT CHECK: FAILED

Detected format:
{logo['format']}

Allowed formats:
PNG, JPG, JPEG, SVG, WEBP

Reason:
Logo format is not compliant with
DBIM requirements.
"""
                )

            else:

                explanations.append(

                    f"""
FORMAT CHECK: PASSED

Detected format:
{logo['format']}

Reason:
Logo format follows DBIM rules.
"""
                )

            # =============================================
            # FILE SIZE
            # =============================================

            if logo["file_size"] > MAX_SIZE_KB:

                compliant = False

                explanations.append(

                    f"""
FILE SIZE CHECK: FAILED

Detected size:
{logo['file_size']} KB

Maximum allowed:
100 KB

Reason:
Logo file size exceeds DBIM limits.
"""
                )

            else:

                explanations.append(

                    f"""
FILE SIZE CHECK: PASSED

Detected size:
{logo['file_size']} KB

Reason:
Logo file size is compliant.
"""
                )

            # =============================================
            # PROPORTION
            # =============================================

            valid = validate_proportion(

                logo["intrinsic_w"],
                logo["intrinsic_h"],

                logo["rendered_w"],
                logo["rendered_h"]

            )

            if not valid:

                compliant = False

                explanations.append(

                    f"""
PROPORTION CHECK: FAILED

Intrinsic dimensions:
{logo['intrinsic_w']}x
{logo['intrinsic_h']}

Rendered dimensions:
{int(logo['rendered_w'])}x
{int(logo['rendered_h'])}

Reason:
The logo appears stretched or
compressed during rendering.
"""
                )

            else:

                explanations.append(

                    f"""
PROPORTION CHECK: PASSED

Reason:
Logo proportions are preserved.
"""
                )

            # =============================================
            # CONTRAST
            # =============================================

            if not validate_contrast(

                logo["display"]

            ):

                compliant = False

                explanations.append(

                    f"""
CONTRAST CHECK: FAILED

Reason:
The logo does not maintain sufficient
contrast against the background.
"""
                )

            else:

                explanations.append(

                    f"""
CONTRAST CHECK: PASSED

Reason:
The logo maintains sufficient
visual contrast.
"""
                )

            # =============================================
            # EXPECTED LOGO
            # =============================================

            expected = generate_expected_logo(

                logo["asset"],

                logo["rendered_w"],
                logo["rendered_h"]

            )

            panel = (

                f"comparison/logo_{idx}.png"
            )

            create_panel(

                logo["display"],
                expected,
                panel,
                compliant

            )

            reason = "\n".join(explanations)

            status = (

                "COMPLIANT"

                if compliant

                else "NON-COMPLIANT"

            )

            print(

                "\n================================"
            )

            print(

                f"LOGO {idx}"
            )

            print(

                "================================"
            )

            print(status)

            print(reason)

            report.append({

                "logo": idx,

                "status": status,

                "reason": reason,

                "comparison": panel

            })



        generate_docx(report)

        await browser.close()

# =========================================================
# RUN
# =========================================================

asyncio.run(
    logo_engine()
)
