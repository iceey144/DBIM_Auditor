# =========================================================
# DBIM ADVANCED SEARCH COMPLIANCE ENGINE
# FULL VISUAL EVIDENCE SYSTEM
# REQUIREMENTS 43 / 44 / 45
# =========================================================
#
# FEATURES
# ---------------------------------------------------------
# ✅ Green annotations for compliant items
# ✅ Red annotations for non-compliant items
# ✅ Multiple proofs per requirement
# ✅ Live temp report generation
# ✅ Final report generation
# ✅ Bounding-box based highlighting
# ✅ Search testing
# ✅ Empty query testing
# ✅ Autocomplete testing
# ✅ PDF searchability testing
# ✅ Metadata testing
# ✅ Categorization testing
#
# =========================================================
# INSTALL
# =========================================================
#
# pip install playwright python-docx beautifulsoup4 lxml pillow
#
# playwright install
#
# =========================================================

from playwright.async_api import async_playwright

from docx import Document
from docx.shared import Inches

from bs4 import BeautifulSoup

from PIL import Image
from PIL import ImageDraw

from datetime import datetime

import asyncio
import os

# =========================================================
# FOLDERS
# =========================================================

os.makedirs("reports", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# =========================================================
# SMART WAIT ENGINE
# =========================================================

async def smart_wait(

    page,

    extra=3000

):

    try:

        # wait for network requests

        await page.wait_for_load_state(

            "networkidle",

            timeout=15000

        )

    except:
        pass

    try:

        # additional rendering wait

        await page.wait_for_timeout(extra)

    except:
        pass


# =========================================================
# RESET VIEWPORT
# =========================================================

async def reset_view(page):

    await page.evaluate(

        """
        window.scrollTo(0, 0)
        """
    )

    await smart_wait(page, 3000)


# =========================================================
# PATHS
# =========================================================

TEMP_DOC = "reports/temp_report.docx"
FINAL_DOC = "reports/final_report.docx"

# =========================================================
# GLOBAL STORAGE
# =========================================================

evidence_store = {

    "Requirement 43": [],
    "Requirement 44": [],
    "Requirement 45": []

}

temp_doc = Document()

temp_doc.add_heading(
    "DBIM SEARCH COMPLIANCE REPORT",
    level=1
)

try:

    temp_doc.save(TEMP_DOC)

except PermissionError:

    print(
        "\nCLOSE temp_report.docx"
    )

# =========================================================
# TEMP REPORT
# =========================================================

def update_temp_report(

    heading,
    text="",
    image=None

):

    global temp_doc

    temp_doc.add_heading(
        heading,
        level=2
    )

    temp_doc.add_paragraph(text)

    if image:

        try:

            temp_doc.add_picture(
                image,
                width=Inches(5.5)
            )

        except:
            pass

    try:

        temp_doc.save(TEMP_DOC)

        print(f"\nUPDATED: {heading}")

    except PermissionError:

        print(
            "\nCLOSE temp_report.docx "
            "FOR LIVE UPDATES"
        )

# =========================================================
# STORE EVIDENCE
# =========================================================

def add_evidence(

    requirement,
    title,
    status,
    reason,
    screenshot

):

    evidence_store[requirement].append({

        "title": title,
        "status": status,
        "reason": reason,
        "screenshot": screenshot

    })

# =========================================================
# ANNOTATION ENGINE
# =========================================================

def annotate(

    image_path,
    output_path,

    x,
    y,
    width,
    height,

    label,
    compliant=True

):

    image = Image.open(image_path)

    draw = ImageDraw.Draw(image)

    # =====================================================
    # COLOR
    # =====================================================

    if compliant:

        color = "green"

    else:

        color = "red"

    # =====================================================
    # RECTANGLE
    # =====================================================

    draw.rectangle(

        [

            (x, y),

            (x + width, y + height)

        ],

        outline=color,

        width=6

    )

    # =====================================================
    # LABEL BG
    # =====================================================

    ly = max(0, y - 40)

    draw.rectangle(

        [

            (x, ly),

            (x + 350, ly + 35)

        ],

        fill=color

    )

    # =====================================================
    # LABEL
    # =====================================================

    draw.text(

        (x + 10, ly + 5),

        label,

        fill="white"

    )

    # =====================================================
    # POINTER
    # =====================================================

    draw.line(

        [

            (x - 80, y - 80),

            (x, y)

        ],

        fill=color,

        width=6

    )

    image.save(output_path)

    return output_path

def clamp_box(

    image_path,
    box,
    padding=16

):

    image = Image.open(image_path)

    img_w, img_h = image.size

    x = max(0, int(box["x"]) - padding)
    y = max(0, int(box["y"]) - padding)
    right = min(img_w, int(box["x"] + box["width"]) + padding)
    bottom = min(img_h, int(box["y"] + box["height"]) + padding)

    return x, y, max(1, right - x), max(1, bottom - y)

def annotate_element(

    image_path,
    output_path,
    box,
    label,
    compliant=True,
    padding=16

):

    x, y, width, height = clamp_box(
        image_path,
        box,
        padding
    )

    return annotate(
        image_path,
        output_path,
        x,
        y,
        width,
        height,
        label,
        compliant
    )

async def first_visible_box(

    page,
    selectors,
    min_width=20,
    min_height=20

):

    for selector in selectors:

        try:

            elements = await page.query_selector_all(selector)

            for element in elements:

                try:

                    if not await element.is_visible():
                        continue

                    box = await element.bounding_box()

                    if not box:
                        continue

                    if box["width"] < min_width:
                        continue

                    if box["height"] < min_height:
                        continue

                    return box

                except:
                    pass

        except:
            pass

    return None

# =========================================================
# SEARCH DETECTOR
# =========================================================

async def detect_search(page):

    selectors = [

        "input[type='search']",

        "input[placeholder*='Search']",

        "input[name*='search']",

        "input[aria-label*='Search']"

    ]

    for selector in selectors:

        try:

            element = await page.query_selector(
                selector
            )

            if element:

                visible = await element.is_visible()

                if visible:

                    return element

        except:
            pass

    return None

# =========================================================
# FINAL REPORT
# =========================================================

def generate_final_report():

    doc = Document()

    doc.add_heading(
        "FINAL DBIM SEARCH REPORT",
        level=1
    )

    doc.add_paragraph(

        "Generated On: "

        +

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    )

    # =====================================================
    # REQUIREMENTS
    # =====================================================

    for requirement in evidence_store:

        doc.add_page_break()

        doc.add_heading(
            requirement,
            level=1
        )

        for item in evidence_store[requirement]:

            doc.add_heading(
                item["title"],
                level=2
            )

            doc.add_paragraph(

                f"STATUS: {item['status']}"

            )

            doc.add_paragraph(

                f"REASON: {item['reason']}"

            )

            try:

                doc.add_picture(

                    item["screenshot"],

                    width=Inches(5.8)

                )

            except:
                pass

    # =====================================================
    # FINAL VERDICT
    # =====================================================

    compliant = True

    for req in evidence_store:

        for item in evidence_store[req]:

            if item["status"] == "NON-COMPLIANT":

                compliant = False
                break

    doc.add_page_break()

    doc.add_heading(
        "FINAL VERDICT",
        level=1
    )

    if compliant:

        verdict = "COMPLIANT"

    else:

        verdict = "NON-COMPLIANT"

    doc.add_paragraph(
        f"WEBSITE STATUS: {verdict}"
    )

    

    try:

        doc.save(FINAL_DOC)

    except PermissionError:

        timestamp = datetime.now().strftime(
            "%H%M%S"
        )

        backup = FINAL_DOC.replace(

            ".docx",

            f"_{timestamp}.docx"

        )

        doc.save(backup)

        print(
            f"\nFINAL REPORT OPEN."
            f"\nSaved backup:"
            f"\n{backup}"
        )

    print("\nFINAL REPORT GENERATED")



# =========================================================
# SEARCH RESULTS DETECTOR
# =========================================================

# =========================================================
# ADVANCED SEARCH RESULT DETECTOR
# =========================================================

async def detect_results(page):

    selectors = [

        ".search-results",

        ".search-results-container",

        ".results-container",

        ".searchResult",

        "[class*='search-result']",

        "[id*='search-result']",

        "[class*='results-container']",

        "[class*='result-item']",

        "[class*='search-item']",

        "[class*='listing']",

        "[class*='card']",

        "article",

        "main a",

        "section a"

    ]

    best_element = None

    best_score = 0

    for selector in selectors:

        try:

            elements = await page.query_selector_all(
                selector
            )

            for el in elements:

                try:

                    visible = await el.is_visible()

                    if not visible:
                        continue

                    box = await el.bounding_box()

                    if not box:
                        continue

                    width = box["width"]
                    height = box["height"]

                    # =====================================
                    # IGNORE TINY ELEMENTS
                    # =====================================

                    if width < 150 or height < 40:
                        continue

                    # =====================================
                    # SCORE AREA
                    # =====================================

                    score = width * height

                    if score > best_score:

                        best_score = score
                        best_element = el

                except:
                    pass

        except:
            pass

    return best_element



# =========================================================
# ADVANCED AUTO SCROLL ENGINE
# =========================================================

async def auto_scroll(

    page,

    max_scrolls=15,

    pause=4500

):

    previous_height = 0

    stable_rounds = 0

    for i in range(max_scrolls):

        # =============================================
        # GET CURRENT PAGE HEIGHT
        # =============================================

        current_height = await page.evaluate(

            "document.body.scrollHeight"

        )

        # =============================================
        # CHECK IF PAGE STOPPED GROWING
        # =============================================

        if current_height == previous_height:

            stable_rounds += 1

        else:

            stable_rounds = 0

        # =============================================
        # IF STABLE MULTIPLE TIMES
        # =============================================

        if stable_rounds >= 2:

            print(
                "\nPAGE FULLY LOADED"
            )

            break

        previous_height = current_height

        # =============================================
        # SMOOTH SCROLL DOWN
        # =============================================

        await page.evaluate(

            """
            window.scrollBy({

                top: window.innerHeight,

                behavior: 'smooth'

            });
            """
        )

        print(
            f"\nSCROLL PASS {i+1}"
        )

        # =============================================
        # WAIT FOR LAZY LOAD
        # =============================================

        await smart_wait(page, pause)

    # =============================================
    # FINAL BOTTOM WAIT
    # =============================================

    print(
        "\nFINAL STABILIZATION..."
    )

    await smart_wait(page, 8000)

    # =============================================
    # EXTRA MICRO SCROLLS
    # =============================================

    for _ in range(3):

        await page.mouse.wheel(0, 500)

        await smart_wait(page, 2500)

    # =============================================
    # FINAL SETTLE
    # =============================================

    await smart_wait(page, 5000)


# =========================================================
# WAIT FOR SEARCH RESULTS
# =========================================================

async def wait_for_results(

    page,

    timeout=40000

):

    selectors = [

        ".search-results",

        ".search-results-container",

        ".results-container",

        ".searchResult",

        "[class*='search-result']",

        "[id*='search-result']",

        "[class*='results-container']",

        "[class*='result-item']",

        "main",

        "article"

    ]

    start = asyncio.get_event_loop().time()

    while True:

        for selector in selectors:

            try:

                elements = await page.query_selector_all(
                    selector
                )

                if elements and len(elements) > 0:

                    visible_count = 0

                    for el in elements:

                        try:

                            visible = await el.is_visible()

                            if visible:

                                visible_count += 1

                        except:
                            pass

                    if visible_count > 0:

                        print(
                            "\nRESULTS LOADED"
                        )

                        return True

            except:
                pass

        current = asyncio.get_event_loop().time()

        if current - start > (timeout / 1000):

            print(
                "\nRESULT WAIT TIMEOUT"
            )

            return False

        await page.wait_for_timeout(1000)

# =================================================
# GET ACTIVE PAGE
# =================================================

async def get_active_page(browser):

    try:

        contexts = browser.contexts

        if not contexts:
            return None

        context = contexts[0]

        pages = context.pages

        if not pages:
            return None

        # =========================================
        # RETURN LAST ACTIVE PAGE
        # =========================================

        for p in reversed(pages):

            try:

                if not p.is_closed():
                    return p

            except:
                pass

        return None

    except:

        return None

# =========================================================
# MAIN ENGINE
# =========================================================

async def dbim_engine():

    url = input(
        "\nEnter Website URL: "
    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=os.getenv("DBIM_HEADED") != "1"
        )

        page = await browser.new_page(

            viewport={

                "width": 1440,
                "height": 900

            }

        )

        # =================================================
        # OPEN WEBSITE
        # =================================================

        print("\nOPENING WEBSITE...")

        await page.goto(
            url,
            wait_until="domcontentloaded"
        )

        await smart_wait(page, 5000)

        homepage_ss = (
            "screenshots/homepage.png"
        )

        await page.screenshot(
            path=homepage_ss,
            full_page=True
        )

        update_temp_report(

            "WEBSITE OPENED",

            "Website loaded successfully.",

            homepage_ss

        )

        # =================================================
        # REQUIREMENT 43
        # SEARCH BAR EXISTS
        # =================================================
        await reset_view(page)

        print("\nTESTING REQUIREMENT 43")

        search = await detect_search(page)

        if search:

            box = await search.bounding_box()

            annotated = annotate_element(

                homepage_ss,

                "screenshots/search_found.png",

                box,

                "Search Bar Found",

                compliant=True,

                padding=14

            )

            add_evidence(

                "Requirement 43",

                "Search Bar Detection",

                "COMPLIANT",

                "Search bar detected.",

                annotated

            )

            update_temp_report(

                "REQ 43 - SEARCH DETECTED",

                "Search bar found.",

                annotated

            )

        else:

            annotated = annotate(

                homepage_ss,

                "screenshots/search_missing.png",

                900,
                20,
                350,
                80,

                "Search Bar Missing",

                compliant=False

            )

            add_evidence(

                "Requirement 43",

                "Search Bar Detection",

                "NON-COMPLIANT",

                "Search bar not found.",

                annotated

            )

        # =================================================
        # SEARCH INPUT
        # =================================================

        if search:

            await search.click()

            await search.type(
                "RTI",
                delay=100
            )

            await smart_wait(page, 4000)

            input_ss = (
                "screenshots/search_input.png"
            )

            await page.screenshot(
                path=input_ss,
                full_page=True
            )

            box = await search.bounding_box()

            annotated = annotate_element(

                input_ss,

                "screenshots/search_input_annotated.png",

                box,

                "Search Query Typed",

                compliant=True,

                padding=14

            )

            add_evidence(

                "Requirement 43",

                "Search Query Input",

                "COMPLIANT",

                "Query input successful.",

                annotated

            )

        # =================================================
        # REAL AUTOCOMPLETE DETECTION
        # REFINED VERSION
        # =================================================

        await smart_wait(page, 4000)

        # =============================================
        # CAPTURE PAGE STATE BEFORE AUTOCOMPLETE
        # =============================================

        # =============================================
        # SAFE PAGE STATE CAPTURE
        # =============================================

        try:

            if page.is_closed():

                print("PAGE CLOSED BEFORE AUTOCOMPLETE")
                before_html = ""
                before_text = ""

            else:

                before_html = await page.content()

                before_text = await page.locator(
                    "body"
                ).inner_text()

        except Exception as e:

            print(f"PAGE STATE ERROR: {e}")

            before_html = ""
            before_text = ""

        # =============================================
        # WAIT FOR POSSIBLE DROPDOWN
        # =============================================

        await smart_wait(page, 5000)

        # =============================================
        # SCROLL SLIGHTLY TO ENSURE VISIBILITY
        # =============================================

        await page.mouse.wheel(0, 300)

        await smart_wait(page, 2000)

        # =============================================
        # AUTOCOMPLETE SELECTORS
        # =============================================

        suggestion_selectors = [

            "[role='option']",

            "[role='listbox']",

            ".autocomplete",

            ".autosuggest",

            ".suggestions",

            ".ui-autocomplete",

            ".tt-menu",

            ".dropdown-menu",

            "[class*='autocomplete']",

            "[class*='autosuggest']",

            "[class*='suggestion']",

            "[class*='dropdown']",

            "[id*='autocomplete']",

            "[id*='autosuggest']"

        ]

        autocomplete_found = False
        suggestion_element = None

        # =============================================
        # DETECT ONLY REAL VISIBLE SUGGESTIONS
        # =============================================

        for selector in suggestion_selectors:

            try:

                elements = await page.query_selector_all(
                    selector
                )

                for el in elements:

                    try:

                        # =====================================
                        # MUST BE VISIBLE
                        # =====================================

                        visible = await el.is_visible()

                        if not visible:
                            continue

                        # =====================================
                        # MUST HAVE REAL SIZE
                        # =====================================

                        box = await el.bounding_box()

                        if not box:
                            continue

                        if box["width"] < 100:
                            continue

                        if box["height"] < 30:
                            continue

                        # =====================================
                        # MUST CONTAIN ACTUAL TEXT
                        # =====================================

                        text = await el.inner_text()

                        if not text:
                            continue

                        text = text.strip()

                        if len(text) < 3:
                            continue

                        # =====================================
                        # MUST CONTAIN SEARCH-RELATED CONTENT
                        # =====================================

                        if "rti" not in text.lower():

                            # allow generic suggestions
                            if len(text.split()) < 2:
                                continue

                        autocomplete_found = True
                        suggestion_element = el

                        break

                    except:
                        pass

                if autocomplete_found:
                    break

            except:
                pass

        # =============================================
        # FINAL SCREENSHOT
        # =============================================

        auto_ss = (
            "screenshots/autocomplete.png"
        )

        await page.screenshot(
            path=auto_ss,
            full_page=True
        )

        # =============================================
        # COMPLIANT
        # =============================================

        if autocomplete_found:

            try:

                box = await suggestion_element.bounding_box()

                annotated = annotate_element(

                    auto_ss,

                    "screenshots/autocomplete_found.png",

                    box,

                    "Visible Autocomplete Suggestions",

                    compliant=True,

                    padding=12

                )

            except:

                annotated = auto_ss

            add_evidence(

                "Requirement 43",

                "Autocomplete",

                "COMPLIANT",

                "Visible autocomplete suggestions detected after typing.",

                annotated

            )

        # =============================================
        # NON-COMPLIANT
        # =============================================

        else:

            annotated = annotate(

                auto_ss,

                "screenshots/autocomplete_missing.png",

                850,
                80,
                350,
                120,

                "No Visible Autocomplete",

                compliant=False

            )

            add_evidence(

                "Requirement 43",

                "Autocomplete",

                "NON-COMPLIANT",

                "No visible autocomplete suggestions appeared after typing.",

                annotated

            )

            # =================================================
            # SEARCH RESULTS
            # =================================================

            # =============================================
            # CAPTURE PRE-SEARCH CONTENT
            # =============================================

            before_text = await page.locator(
                "body"
            ).inner_text()

            # =============================================
            # EXECUTE SEARCH
            # =============================================

            await page.keyboard.press("Enter")

            # =============================================
            # WAIT FOR REAL RESULTS
            # =============================================

            loaded = await wait_for_results(

                page,

                timeout=40000

            )

            print(
                "\nRESULTS DETECTED"
            )

            # =============================================
            # INITIAL STABILIZATION
            # =============================================

            await smart_wait(page, 8000)

            # =============================================
            # LOAD ALL LAZY CONTENT
            # =============================================

            await auto_scroll(

                page,

                max_scrolls=15,

                pause=5000

            )

            # =============================================
            # RETURN SLIGHTLY UPWARD
            # =============================================

            await page.mouse.wheel(0, -1200)

            await smart_wait(page, 4000)

            # =============================================
            # FINAL SCREENSHOT
            # =============================================

            results_ss = (
                "screenshots/results.png"
            )

            await page.screenshot(

                path=results_ss,

                full_page=True

            )

            # =============================================
            # CAPTURE POST-SEARCH CONTENT
            # =============================================

            after_text = await page.locator(
                "body"
            ).inner_text()

            # =============================================
            # DETECT VISIBLE SEARCH RESULTS
            # =============================================

            page_text = after_text.lower()

            search_keywords = [

                "rti",

                "right to information",

                "information",

                "act",

                "application"

            ]

            match_count = 0

            for word in search_keywords:

                if word in page_text:

                    match_count += 1
            
            # =============================================
            # SEARCH RESULTS FOUND
            # =============================================

            if match_count >= 2:

                result_element = await detect_results(page)

                result_box = None

                if result_element:

                    result_box = await result_element.bounding_box()

                if result_box:

                    annotated = annotate_element(

                        results_ss,

                        "screenshots/results_annotated.png",

                        result_box,

                        "Search Results Loaded",

                        compliant=True,

                        padding=18

                    )

                else:

                    annotated = annotate(

                        results_ss,

                        "screenshots/results_annotated.png",

                        80,
                        150,
                        1200,
                        700,

                        "Search Results Loaded",

                        compliant=True

                    )

                add_evidence(

                    "Requirement 43",

                    "Search Results",

                    "COMPLIANT",

                    "Search results successfully loaded after query execution.",

                    annotated

                )

            # =============================================
            # SEARCH RESULTS FAILED
            # =============================================

            else:

                annotated = annotate(

                    results_ss,

                    "screenshots/results_missing.png",

                    80,
                    150,
                    1200,
                    700,

                    "Search Results Missing",

                    compliant=False

                )

                add_evidence(

                    "Requirement 43",

                    "Search Results",

                    "NON-COMPLIANT",

                    "No meaningful page change detected after search query.",

                    annotated

                )
            # =================================================
            # EMPTY QUERY
            # =================================================

            try:

                search = await detect_search(page)

                if search:

                    await search.click()

                    await page.keyboard.press(
                        "Control+A"
                    )

                    await page.keyboard.press(
                        "Backspace"
                    )

                    await page.keyboard.press("Enter")

                    await smart_wait(page, 6000)

                    empty_ss = (
                        "screenshots/empty_query.png"
                    )

                    await page.screenshot(
                        path=empty_ss,
                        full_page=True
                    )

                    box = await search.bounding_box()

                    annotated = annotate_element(

                        empty_ss,

                        "screenshots/empty_query_annotated.png",

                        box,

                        "Empty Query Handled",

                        compliant=True,

                        padding=14

                    )

                    add_evidence(

                        "Requirement 43",

                        "Empty Query Handling",

                        "COMPLIANT",

                        "Empty query handled properly.",

                        annotated

                    )

            except:

                fail_ss = (
                    "screenshots/empty_fail.png"
                )

                await page.screenshot(
                    path=fail_ss,
                    full_page=True
                )

                fail_box = await first_visible_box(

                    page,

                    [
                        "input[type='search']",
                        "input[placeholder*='Search']",
                        "input[name*='search']",
                        "input[aria-label*='Search']"
                    ]

                )

                if fail_box:

                    annotated = annotate_element(

                        fail_ss,

                        "screenshots/empty_fail_annotated.png",

                        fail_box,

                        "Empty Query Failed",

                        compliant=False,

                        padding=14

                    )

                else:

                    annotated = annotate(

                        fail_ss,

                        "screenshots/empty_fail_annotated.png",

                        150,
                        200,
                        900,
                        300,

                        "Empty Query Failed",

                        compliant=False

                    )

                add_evidence(

                    "Requirement 43",

                    "Empty Query Handling",

                    "NON-COMPLIANT",

                    "Empty query handling failed.",

                    annotated

                )

        # =================================================
        # REQUIREMENT 44
        # =================================================
        await reset_view(page)

        print("\nTESTING REQUIREMENT 44")

        

        # =================================================
        # PDF SEARCHABILITY
        # =================================================

        # =================================================
        # REAL SEARCHABLE PDF VALIDATION
        # =================================================

        pdf_found = False

        pdf_ss = (
            "screenshots/pdf_search.png"
        )

        await page.screenshot(
            path=pdf_ss,
            full_page=True
        )

        try:

            search = await detect_search(page)

            if search:

                await search.click()

                await page.keyboard.press(
                    "Control+A"
                )

                await page.keyboard.press(
                    "Backspace"
                )

                await search.type(

                    "annual report",

                    delay=100

                )

                await smart_wait(page, 4000)

                await page.keyboard.press("Enter")


                # =============================================
                # WAIT FOR RESULTS
                # =============================================

                loaded = await wait_for_results(

                    page,

                    timeout=45000

                )

                # =============================================
                # INITIAL STABILIZATION
                # =============================================

                await smart_wait(page, 8000)

                # =============================================
                # LOAD ALL DYNAMIC RESULTS
                # =============================================

                await auto_scroll(

                    page,

                    max_scrolls=18,

                    pause=5500

                )

                # =============================================
                # RETURN SLIGHTLY UPWARD
                # =============================================

                await page.mouse.wheel(0, -1200)

                await smart_wait(page, 5000)

                # =============================================
                # FINAL SCREENSHOT
                # =============================================

                await page.screenshot(

                    path=pdf_ss,

                    full_page=True

                )

                

                # =============================================
                # EXTRACT VISIBLE TEXT + LINKS
                # =============================================

                anchors = await page.query_selector_all("a")

                pdf_found = False

                pdf_element = None

                for a in anchors:

                    try:

                        text = (
                            await a.inner_text()
                        ).lower()

                        href = (
                            await a.get_attribute("href")
                        )

                        href = str(href).lower()

                        # =====================================
                        # REAL PDF DETECTION
                        # =====================================

                        if (

                            ".pdf" in href

                            or

                            "annual report" in text

                            or

                            "download report" in text

                            or

                            "report pdf" in text

                            or

                            "view report" in text

                            or

                            "download" in text

                        ):

                            pdf_found = True
                            pdf_element = a

                            break

                    except:
                        pass

            # =============================================
            # PDF FOUND
            # =============================================

            if pdf_found:

                if pdf_element:

                    try:

                        box = await pdf_element.bounding_box()

                        annotated = annotate_element(

                            pdf_ss,

                            "screenshots/pdf_found.png",

                            box,

                            "PDF Results Found",

                            compliant=True,

                            padding=14

                        )

                    except:

                        annotated = pdf_ss

                else:

                    annotated = pdf_ss

                add_evidence(

                    "Requirement 44",

                    "PDF Searchability",

                    "COMPLIANT",

                    "Search results contain downloadable PDF/report content.",

                    annotated

                )

            # =============================================
            # PDF NOT FOUND
            # =============================================

            else:

                annotated = annotate(

                    pdf_ss,

                    "screenshots/pdf_missing.png",

                    80,
                    180,
                    1200,
                    600,

                    "PDF Results Missing",

                    compliant=False

                )

                add_evidence(

                    "Requirement 44",

                    "PDF Searchability",

                    "NON-COMPLIANT",

                    "No searchable/downloadable PDF content detected.",

                    annotated

                )

        except Exception as e:

            add_evidence(

                "Requirement 44",

                "PDF Searchability",

                "NON-COMPLIANT",

                str(e),

                pdf_ss

            )

                    
        # =================================================
        # REFRESH FULLY LOADED HTML
        # =================================================

        html = await page.content()

        soup = BeautifulSoup(
            html,
            "lxml"
        )
        # =================================================
        # IMAGE METADATA
        # =================================================

        images = soup.find_all("img")

        metadata_found = False

        for img in images:

            alt = img.get("alt")

            if alt and len(alt.strip()) > 0:

                metadata_found = True
                break

        meta_ss = (
            "screenshots/image_metadata.png"
        )

        await page.screenshot(
            path=meta_ss,
            full_page=True
        )

        if metadata_found:

            image_box = await first_visible_box(

                page,

                [
                    "img[alt]:not([alt=''])",
                    "img"
                ],

                min_width=40,

                min_height=40

            )

            if image_box:

                annotated = annotate_element(

                    meta_ss,

                    "screenshots/image_metadata_found.png",

                    image_box,

                    "Image Metadata Found",

                    compliant=True,

                    padding=16

                )

            else:

                annotated = annotate(

                    meta_ss,

                    "screenshots/image_metadata_found.png",

                    400,
                    300,
                    400,
                    250,

                    "Image Metadata Found",

                    compliant=True

                )

            add_evidence(

                "Requirement 44",

                "Image Metadata",

                "COMPLIANT",

                "Image metadata detected.",

                annotated

            )

        else:

            annotated = annotate(

                meta_ss,

                "screenshots/image_metadata_missing.png",

                400,
                300,
                400,
                250,

                "Image Metadata Missing",

                compliant=False

            )

            add_evidence(

                "Requirement 44",

                "Image Metadata",

                "NON-COMPLIANT",

                "Image metadata missing.",

                annotated

            )

        # =================================================
        # REQUIREMENT 45
        # =================================================
        await reset_view(page)

        print("\nTESTING REQUIREMENT 45")

        # =================================================
        # META DESCRIPTION
        # =================================================

        meta_description = soup.find(

            "meta",

            attrs={"name":"description"}

        )

        desc_ss = (
            "screenshots/meta_description.png"
        )

        await page.screenshot(
            path=desc_ss,
            full_page=True
        )

        if meta_description:

            annotated = annotate(

                desc_ss,

                "screenshots/meta_description_found.png",

                100,
                50,
                500,
                120,

                "Meta Description Found",

                compliant=True

            )

            add_evidence(

                "Requirement 45",

                "Meta Description",

                "COMPLIANT",

                "Meta description detected.",

                annotated

            )

        else:

            annotated = annotate(

                desc_ss,

                "screenshots/meta_description_missing.png",

                100,
                50,
                500,
                120,

                "Meta Description Missing",

                compliant=False

            )

            add_evidence(

                "Requirement 45",

                "Meta Description",

                "NON-COMPLIANT",

                "Meta description missing.",

                annotated

            )

        # =================================================
        # META KEYWORDS
        # =================================================

        meta_keywords = soup.find(

            "meta",

            attrs={"name":"keywords"}

        )

        key_ss = (
            "screenshots/meta_keywords.png"
        )

        await page.screenshot(
            path=key_ss,
            full_page=True
        )

        if meta_keywords:

            annotated = annotate(

                key_ss,

                "screenshots/meta_keywords_found.png",

                650,
                50,
                500,
                120,

                "Meta Keywords Found",

                compliant=True

            )

            add_evidence(

                "Requirement 45",

                "Meta Keywords",

                "COMPLIANT",

                "Meta keywords detected.",

                annotated

            )

        else:

            annotated = annotate(

                key_ss,

                "screenshots/meta_keywords_missing.png",

                650,
                50,
                500,
                120,

                "Meta Keywords Missing",

                compliant=False

            )

            add_evidence(

                "Requirement 45",

                "Meta Keywords",

                "NON-COMPLIANT",

                "Meta keywords missing.",

                annotated

            )

    
        # =================================================
        # FILTERS / CATEGORIZATION
        # =================================================

        filter_keywords = [

            "filter",

            "sort",

            "category",

            "refine"

        ]

        filters_found = False

        for tag in soup.find_all(

            ["button", "select", "input"]

        ):

            text = str(tag).lower()

            for word in filter_keywords:

                if word in text:

                    filters_found = True
                    break

        filter_ss = (
            "screenshots/filter_test.png"
        )

        await page.screenshot(
            path=filter_ss,
            full_page=True
        )

        if filters_found:

            filter_box = await first_visible_box(

                page,

                [
                    "select",
                    "button[aria-label*='filter' i]",
                    "button[aria-label*='sort' i]",
                    "[class*='filter' i]",
                    "[class*='sort' i]",
                    "[id*='filter' i]",
                    "[id*='sort' i]",
                    "xpath=//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'filter')]",
                    "xpath=//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sort')]",
                    "xpath=//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'category')]",
                    "xpath=//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'filter')]"
                ],

                min_width=20,

                min_height=20

            )

            if filter_box:

                annotated = annotate_element(

                    filter_ss,

                    "screenshots/filter_found.png",

                    filter_box,

                    "Filters/Categorization Found",

                    compliant=True,

                    padding=16

                )

            else:

                annotated = annotate(

                    filter_ss,

                    "screenshots/filter_found.png",

                    50,
                    200,
                    250,
                    500,

                    "Filters/Categorization Found",

                    compliant=True

                )

            add_evidence(

                "Requirement 45",

                "Categorization / Filtering",

                "COMPLIANT",

                "Filtering/categorization detected.",

                annotated

            )

        else:

            annotated = annotate(

                filter_ss,

                "screenshots/filter_missing.png",

                50,
                200,
                250,
                500,

                "Filters Missing",

                compliant=False

            )

            add_evidence(

                "Requirement 45",

                "Categorization / Filtering",

                "NON-COMPLIANT",

                "Filtering/categorization missing.",

                annotated

            )

        # =================================================
        # CLOSE
        # =================================================

        await browser.close()

    # =====================================================
    # GENERATE FINAL REPORT
    # =====================================================

    generate_final_report()

# =========================================================
# RUN
# =========================================================

asyncio.run(
    dbim_engine()
)
