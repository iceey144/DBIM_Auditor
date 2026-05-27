# =========================================================
# DBIM ADVANCED ICONOGRAPHY COMPLIANCE ENGINE
# PROFESSIONAL REFINED VERSION
# =========================================================
#
# CORE ARCHITECTURE
# ---------------------------------------------------------
# 1. ORIGINAL ASSET EXTRACTION
#    - SVG source
#    - IMG source
#    - CSS background image
#    - Font icons
#
# 2. DISPLAY ANALYSIS
#    - actual rendered size
#    - css distortion
#    - scaling
#    - alignment
#    - contrast
#
# 3. EXPECTED DBIM GENERATION
#    - uses ORIGINAL asset
#    - generates compliant rendering
#
# 4. SIDE-BY-SIDE COMPARISON
#    - current display
#    - original asset
#    - expected DBIM
#
# 5. RULE-BASED VALIDATION
#    - NO HEATMAPS
#    - NO PIXEL DIFFERENCE
#
# =========================================================
# INSTALL
# =========================================================
#
# pip install playwright pillow python-docx
# pip install opencv-python-headless numpy requests cairosvg
#
# playwright install
#
# =========================================================

import asyncio
import os
import requests
import cv2
import numpy as np

from io import BytesIO
from datetime import datetime

from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps

from docx import Document
from docx.shared import Inches

from playwright.async_api import async_playwright



# =========================================================
# FOLDERS
# =========================================================

folders = [

    "assets",
    "displayed",
    "expected",
    "comparison",
    "annotated",
    "screenshots",
    "reports"

]

for folder in folders:

    os.makedirs(folder, exist_ok=True)

# =========================================================
# DBIM RULES
# =========================================================

VALID_SIZES = [

    24,
    32,
    48,
    64

]

# =========================================================
# RESULTS
# =========================================================

results = []

# =========================================================
# WAIT
# =========================================================

async def smart_wait(page, extra=5000):

    try:

        await page.wait_for_load_state(

            "networkidle",

            timeout=25000

        )

    except:
        pass

    await page.wait_for_timeout(extra)

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

            if clip["width"] <= 0:
                return False

            if clip["height"] <= 0:
                return False

            await page.screenshot(

                path=path,
                clip=clip

            )

        else:

            await page.screenshot(

                path=path,
                full_page=True

            )

        # =============================================
        # VERIFY FILE EXISTS
        # =============================================

        if not os.path.exists(path):

            return False

        img = cv2.imread(path)

        if img is None:

            return False

        h, w = img.shape[:2]

        if w < 5:
            return False

        if h < 5:
            return False

        return True

    except Exception as e:

        print(

            f"\nSCREENSHOT FAILED: {path}"

        )

        print(str(e))

        return False
# =========================================================
# DOWNLOAD IMAGE
# =========================================================

def download_image(

    url,
    out

):

    try:

        r = requests.get(

            url,
            timeout=15

        )

        if r.status_code == 200:

            with open(out, "wb") as f:

                f.write(r.content)

            return True

    except:
        pass

    return False

# =========================================================
# SVG TO PNG
# =========================================================


# =========================================================
# STYLE DETECTION
# =========================================================

def detect_style(path):

    img = cv2.imread(path)

    if img is None:
        return "line"

    gray = cv2.cvtColor(

        img,
        cv2.COLOR_BGR2GRAY

    )

    _, thresh = cv2.threshold(

        gray,
        220,
        255,
        cv2.THRESH_BINARY_INV

    )

    contours, _ = cv2.findContours(

        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE

    )

    if not contours:
        return "line"

    areas = []

    hulls = []

    for c in contours:

        area = cv2.contourArea(c)

        hull = cv2.convexHull(c)

        hull_area = cv2.contourArea(hull)

        if area > 0:

            areas.append(area)
            hulls.append(hull_area)

    if not areas:
        return "line"

    solidity = (

        np.mean(areas)
        /
        np.mean(hulls)

    )

    if solidity > 0.65:

        return "filled"

    return "line"

# =========================================================
# EXPECTED DBIM GENERATION
# =========================================================

# =========================================================
# EXPECTED DBIM GENERATION
# REALISTIC WEBSITE-COMPLIANT RENDERING
# =========================================================

def generate_expected_icon(

    asset_path,
    rendered_width,
    rendered_height

):

    # =============================================
    # LOAD ORIGINAL ASSET
    # =============================================

    img = Image.open(

        asset_path

    ).convert("RGBA")

    # =============================================
    # REMOVE EMPTY PADDING
    # =============================================

    alpha = img.split()[-1]

    bbox = alpha.getbbox()

    if bbox:

        img = img.crop(bbox)

    ow, oh = img.size

    # =============================================
    # PRESERVE ORIGINAL APPEARANCE
    # =============================================
    #
    # IMPORTANT:
    # NO threshold
    # NO canny
    # NO edge detection
    # NO style reconstruction
    #
    # We preserve:
    # - fills
    # - gradients
    # - colors
    # - branding
    # - shadows
    # - exact appearance
    #
    # =============================================

    # =============================================
    # CHOOSE NEAREST DBIM SIZE
    # =============================================

    nearest = min(

        VALID_SIZES,

        key=lambda s:

        abs(s - rendered_width)

        +

        abs(s - rendered_height)

    )

    # =============================================
    # PRESERVE ASPECT RATIO
    # =============================================

    scale = min(

        nearest / ow,
        nearest / oh

    )

    nw = int(ow * scale)
    nh = int(oh * scale)

    # =============================================
    # HIGH QUALITY RESIZE
    # =============================================

    resized = img.resize(

        (nw, nh),

        Image.LANCZOS

    )

    # =============================================
    # DBIM COMPLIANT CANVAS
    # =============================================

    canvas_size = max(

        nearest + 16,
        64

    )

    canvas = Image.new(

        "RGBA",

        (canvas_size, canvas_size),

        (255,255,255,0)

    )

    # =============================================
    # CENTER ALIGNMENT
    # =============================================

    x = (canvas_size - nw) // 2
    y = (canvas_size - nh) // 2

    canvas.paste(

        resized,

        (x,y),

        resized

    )

    # =============================================
    # RETURN REALISTIC RESULT
    # =============================================

    return cv2.cvtColor(

        np.array(canvas),

        cv2.COLOR_RGBA2BGR

    )

# =========================================================
# SIZE VALIDATION
# =========================================================

def validate_size(

    width,
    height

):

    for s in VALID_SIZES:

        if abs(width-s) <= 6:

            if abs(height-s) <= 6:

                return True

    return False

# =========================================================
# PROPORTION VALIDATION
# =========================================================

def validate_proportion(

    width,
    height

):

    ratio = width / height

    if ratio < 0.8:
        return False

    if ratio > 1.2:
        return False

    return True

# =========================================================
# ALIGNMENT VALIDATION
# =========================================================

def validate_alignment(path):

    img = cv2.imread(path)

    if img is None:
        return False

    gray = cv2.cvtColor(

        img,
        cv2.COLOR_BGR2GRAY

    )

    _, thresh = cv2.threshold(

        gray,
        220,
        255,
        cv2.THRESH_BINARY_INV

    )

    moments = cv2.moments(thresh)

    if moments["m00"] == 0:
        return False

    cx = int(

        moments["m10"]
        /
        moments["m00"]

    )

    cy = int(

        moments["m01"]
        /
        moments["m00"]

    )

    h,w = thresh.shape

    dx = abs(cx - w//2)
    dy = abs(cy - h//2)

    if dx > 10:
        return False

    if dy > 10:
        return False

    return True

# =========================================================
# CONTRAST VALIDATION
# =========================================================

def validate_contrast(path):

    img = cv2.imread(path)

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
    asset,
    expected,
    output,
    compliant

):

    img1 = cv2.imread(current)
    img2 = cv2.imread(asset)

    img3 = expected

    img1 = cv2.resize(
        img1,
        (220,220)
    )

    img2 = cv2.resize(
        img2,
        (220,220)
    )

    img3 = cv2.resize(
        img3,
        (220,220)
    )

    canvas = np.ones(

        (

            360,
            760,
            3

        ),

        dtype=np.uint8

    ) * 255

    canvas[
        80:300,
        20:240
    ] = img1

    canvas[
        80:300,
        270:490
    ] = img2

    canvas[
        80:300,
        520:740
    ] = img3

    # =============================================
    # LABELS
    # =============================================

    cv2.putText(

        canvas,

        "CURRENT DISPLAY",

        (30,40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0,0,255),

        2

    )

    cv2.putText(

        canvas,

        "ORIGINAL ASSET",

        (285,40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255,0,0),

        2

    )

    cv2.putText(

        canvas,

        "EXPECTED DBIM",

        (535,40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

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

        (250,345),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.9,

        color,

        3

    )

    cv2.imwrite(output, canvas)

# =========================================================
# PAGE ANNOTATION
# =========================================================

def annotate_page(

    screenshot,
    output,
    box,
    compliant,
    text

):

    image = Image.open(screenshot)

    draw = ImageDraw.Draw(image)

    color = "green" if compliant else "red"

    x = int(box["x"])
    y = int(box["y"])

    w = int(box["width"])
    h = int(box["height"])

    draw.rectangle(

        [

            (x,y),
            (x+w,y+h)

        ],

        outline=color,

        width=5

    )

    draw.rectangle(

        [

            (x,max(0,y-90)),
            (min(image.size[0],x+800),max(40,y-40))

        ],

        fill=color

    )

    draw.text(

        (x+10,max(5,y-82)),

        text,

        fill="white"

    )

    image.save(output)

# =========================================================
# EXTRACT ICONS
# =========================================================

async def extract_icons(page):

    selectors = [

        "svg",
        "img",
        "i",
        ".icon",
        "[class*='icon']",
        "[class*='fa-']"

    ]

    icons = []

    idx = 0

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    # =====================================
                    # ENSURE VISIBLE
                    # =====================================

                    visible = await el.is_visible()

                    if not visible:
                        continue

                    # =====================================
                    # SCROLL INTO VIEW
                    # =====================================

                    try:

                        await el.scroll_into_view_if_needed()

                        await page.wait_for_timeout(300)

                    except:
                        pass

                    # =====================================
                    # BOUNDING BOX
                    # =====================================

                    box = await el.bounding_box()

                    if not box:
                        continue

                    if box["width"] < 12:
                        continue

                    if box["height"] < 12:
                        continue

                    # =====================================
                    # FILTER HUGE OBJECTS
                    # =====================================

                    area = (

                        box["width"]
                        *
                        box["height"]

                    )

                    if area > 12000:
                        continue

                    # =====================================
                    # FILTER EXTREME RATIOS
                    # =====================================

                    ratio = (

                        box["width"]
                        /
                        box["height"]

                    )

                    if ratio > 3:
                        continue

                    if ratio < 0.3:
                        continue

                    # =====================================
                    # PAGE SIZE
                    # =====================================

                    page_size = await page.evaluate(

                        """
                        () => ({

                            width:
                            document
                            .documentElement
                            .scrollWidth,

                            height:
                            document
                            .documentElement
                            .scrollHeight

                        })
                        """

                    )

                    # =====================================
                    # SAFE CLIP
                    # =====================================

                    padding = 4

                    clip_x = max(
                        0,
                        box["x"] - padding
                    )

                    clip_y = max(
                        0,
                        box["y"] - padding
                    )

                    clip_right = min(

                        page_size["width"],

                        box["x"]
                        +
                        box["width"]
                        +
                        padding

                    )

                    clip_bottom = min(

                        page_size["height"],

                        box["y"]
                        +
                        box["height"]
                        +
                        padding

                    )

                    # =====================================
                    # INVALID CLIP CHECK
                    # =====================================

                    if clip_right <= clip_x:
                        continue

                    if clip_bottom <= clip_y:
                        continue

                    clip = {

                        "x": clip_x,
                        "y": clip_y,

                        "width":

                            max(
                                1,
                                clip_right - clip_x
                            ),

                        "height":

                            max(
                                1,
                                clip_bottom - clip_y
                            )

                    }

                    # =====================================
                    # DISPLAY SCREENSHOT
                    # =====================================

                    display_path = (

                        f"displayed/icon_{idx}.png"

                    )

                    success = await safe_screenshot(

                        page,
                        display_path,
                        clip

                    )

                    if not success:

                        continue

                    # =====================================
                    # VERIFY IMAGE READABLE
                    # =====================================

                    test_img = cv2.imread(display_path)

                    if test_img is None:

                        continue

                    h, w = test_img.shape[:2]

                    if w < 5:
                        continue

                    if h < 5:
                        continue

                    # =====================================
                    # GET TAG
                    # =====================================

                    tag = await el.evaluate(

                        "e => e.tagName.toLowerCase()"

                    )

                    asset_path = (

                        f"assets/icon_{idx}.png"

                    )

                    asset_type = "unknown"

                    # =====================================
                    # SVG
                    # =====================================

                    if tag == "svg":

                        asset_path = display_path

                        asset_type = "svg"

                    # =====================================
                    # IMG
                    # =====================================

                    elif tag == "img":

                        src = await el.get_attribute(
                            "src"
                        )

                        if src:

                            success = download_image(

                                src,
                                asset_path

                            )

                            if success:

                                asset_type = "img"

                    # =====================================
                    # CSS ICONS
                    # =====================================

                    else:

                        bg = await el.evaluate(

                            """
                            e => getComputedStyle(e)
                            .backgroundImage
                            """

                        )

                        if "url(" in bg:

                            try:

                                url = bg.split("url(")[1]
                                url = url.split(")")[0]

                                url = url.replace(
                                    '"',
                                    ''
                                )

                                url = url.replace(
                                    "'",
                                    ""
                                )

                                success = download_image(

                                    url,
                                    asset_path

                                )

                                if success:

                                    asset_type = "css"

                            except:
                                pass

                    # =====================================
                    # FALLBACK
                    # =====================================

                    if not os.path.exists(asset_path):

                        asset_path = display_path

                    # =====================================
                    # VERIFY ASSET
                    # =====================================

                    asset_img = cv2.imread(asset_path)

                    if asset_img is None:

                        asset_path = display_path

                    # =====================================
                    # CSS STYLES
                    # =====================================

                    styles = await el.evaluate(

                        """
                        e => {

                            const s =
                            getComputedStyle(e);

                            return {

                                width:s.width,
                                height:s.height,

                                color:s.color,

                                background:
                                s.backgroundColor,

                                transform:
                                s.transform,

                                opacity:
                                s.opacity

                            };

                        }
                        """

                    )

                    icons.append({

                        "display": display_path,

                        "asset": asset_path,

                        "asset_type": asset_type,

                        "styles": styles,

                        "box": box,

                        "rendered_width":
                            box["width"],

                        "rendered_height":
                            box["height"]

                    })

                    print(

                        f"\nICON {idx} EXTRACTED"

                    )

                    idx += 1

                except Exception as e:

                    print(

                        "\nICON EXTRACTION ERROR:"
                    )

                    print(str(e))

        except Exception as e:

            print(

                "\nSELECTOR ERROR:"
            )

            print(str(e))

    return icons
# =========================================================
# REPORT
# =========================================================

def generate_report():

    doc = Document()

    doc.add_heading(

        "DBIM ICONOGRAPHY COMPLIANCE REPORT",

        level=1

    )

    doc.add_paragraph(

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    )

    for r in results:

        doc.add_heading(

            r["title"],

            level=2

        )

        doc.add_paragraph(

            f"STATUS: {r['status']}"

        )

        doc.add_paragraph(

            r["reason"]

        )

        doc.add_picture(

            r["comparison"],

            width=Inches(7)

        )

        doc.add_picture(

            r["annotated"],

            width=Inches(7)

        )

    timestamp = datetime.now().strftime(

        "%Y%m%d_%H%M%S"

    )

    report = (

        f"reports/iconography_report_{timestamp}.docx"

    )

    doc.save(report)

    print(

        f"\nREPORT SAVED: {report}"

    )

# =========================================================
# MAIN ENGINE
# =========================================================

async def engine():

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

        await smart_wait(page, 7000)

        full = "screenshots/full.png"

        await safe_screenshot(

            page,
            full

        )

        # =================================================
        # EXTRACT ICONS
        # =================================================

        print("\nEXTRACTING ICONS...")

        icons = await extract_icons(page)

        print(

            f"\nTOTAL ICONS: {len(icons)}"

        )

        if not icons:

            print("\nNO ICONS FOUND")

            return

        # =================================================
        # DOMINANT STYLE
        # =================================================

        styles = []

        for icon in icons:

            styles.append(

                detect_style(
                    icon["asset"]
                )

            )

        dominant_style = max(

            set(styles),

            key=styles.count

        )

        print(

            f"\nDOMINANT STYLE: "
            f"{dominant_style}"

        )

        # =================================================
        # ANALYSIS
        # =================================================

        for idx, icon in enumerate(icons):

            compliant = True

            reasons = []

            asset = icon["asset"]

            display = icon["display"]

            width = icon["rendered_width"]
            height = icon["rendered_height"]

            # =============================================
            # STYLE
            # =============================================

            style = detect_style(asset)

            if style != dominant_style:

                compliant = False

        
            # =============================================
            # EXPLAINABLE ANALYSIS
            # =============================================

            explanations = []

            # =============================================
            # STYLE
            # =============================================

            style = detect_style(asset)

            if style != dominant_style:

                compliant = False

                explanations.append(

                    f"""
            STYLE CHECK: FAILED

            Detected icon style:
            {style}

            Dominant website icon style:
            {dominant_style}

            Reason:
            This icon visually differs from the
            dominant icon system used across
            the website.

            DBIM requires visual consistency
            across iconography.
            """
                )

            else:

                explanations.append(

                    f"""
            STYLE CHECK: PASSED

            Detected icon style:
            {style}

            Reason:
            The icon style matches the dominant
            visual icon language used on the
            website.
            """
                )

            # =============================================
            # SIZE
            # =============================================

            nearest = min(

                VALID_SIZES,

                key=lambda s:

                abs(s-width)
                +
                abs(s-height)

            )

            if not validate_size(

                width,
                height

            ):

                compliant = False

                explanations.append(

                    f"""
            SIZE CHECK: FAILED

            Detected rendered size:
            {int(width)} x {int(height)} px

            Nearest DBIM size:
            {nearest} x {nearest} px

            Allowed DBIM sizes:
            24x24, 32x32, 48x48, 64x64

            Reason:
            The displayed icon dimensions do
            not conform to standard DBIM icon
            sizes.
            """
                )

            else:

                explanations.append(

                    f"""
            SIZE CHECK: PASSED

            Detected rendered size:
            {int(width)} x {int(height)} px

            Reason:
            The displayed icon dimensions fall
            within acceptable DBIM icon size
            standards.
            """
                )

            # =============================================
            # PROPORTION
            # =============================================

            ratio = round(

                width / height,

                2

            )

            if not validate_proportion(

                width,
                height

            ):

                compliant = False

                explanations.append(

                    f"""
            PROPORTION CHECK: FAILED

            Detected aspect ratio:
            {ratio}

            Expected aspect ratio:
            1.0

            Reason:
            The icon appears visually stretched
            or compressed during website
            rendering.

            This usually occurs due to CSS
            width/height distortion.
            """
                )

            else:

                explanations.append(

                    f"""
            PROPORTION CHECK: PASSED

            Detected aspect ratio:
            {ratio}

            Reason:
            The icon proportions are preserved
            correctly during rendering.
            """
                )

            # =============================================
            # ALIGNMENT
            # =============================================

            if not validate_alignment(asset):

                compliant = False

                explanations.append(

                    f"""
            ALIGNMENT CHECK: FAILED

            Reason:
            The icon content is not visually
            centered inside its rendering area.

            DBIM requires balanced spacing and
            centered icon alignment.
            """
                )

            else:

                explanations.append(

                    f"""
            ALIGNMENT CHECK: PASSED

            Reason:
            The icon content is properly centered
            within its rendering space.
            """
                )

            # =============================================
            # CONTRAST
            # =============================================

            if not validate_contrast(display):

                compliant = False

                explanations.append(

                    f"""
            CONTRAST CHECK: FAILED

            Reason:
            The icon does not maintain sufficient
            visual contrast against its
            background.

            This reduces visibility and
            accessibility.
            """
                )

            else:

                explanations.append(

                    f"""
            CONTRAST CHECK: PASSED

            Reason:
            The icon maintains sufficient visual
            contrast against its background.
            """
                )

            # =============================================
            # FINAL EXPLANATION
            # =============================================

            reason = "\n\n".join(explanations)
            # =============================================
            # EXPECTED
            # =============================================

            expected = generate_expected_icon(

                asset,

                width,
                height

            )

            # =============================================
            # PANEL
            # =============================================

            panel = (

                f"comparison/icon_{idx}.png"

            )

            create_panel(

                display,
                asset,
                expected,
                panel,
                compliant

            )

            # =============================================
            # PAGE ANNOTATION
            # =============================================

            ann = (

                f"annotated/icon_{idx}.png"

            )

            annotate_page(

                full,
                ann,
                icon["box"],
                compliant,

                "COMPLIANT"

                if compliant

                else

                "NON-COMPLIANT"

            )

            # =============================================
            # FINAL
            # =============================================

            if compliant:

                reason = (

                    "Original asset and rendered "
                    "display comply with DBIM "
                    "guidelines for style, "
                    "size, proportion, "
                    "alignment and contrast."

                )

                status = "COMPLIANT"

            else:

                reason = "\n".join(reasons)

                status = "NON-COMPLIANT"

            results.append({

                "title":

                    f"Icon {idx}",

                "status":
                    status,

                "reason":
                    reason,

                "comparison":
                    panel,

                "annotated":
                    ann

            })

        await browser.close()

    # =====================================================
    # REPORT
    # =====================================================

    generate_report()

    print("\nFINAL REPORT GENERATED")

# =========================================================
# RUN
# =========================================================

asyncio.run(
    engine()
)
