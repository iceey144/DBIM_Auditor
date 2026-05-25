# =========================================================
# DBIM PERFORMANCE ENHANCEMENT AUDITOR
# FULL REFINED VERSION
# =========================================================
#
# FEATURES
# ---------------------------------------------------------
# ✅ Real Performance Metrics
# ✅ Real Load Timings
# ✅ TTFB Detection
# ✅ DOM Interactive Time
# ✅ Lazy Loading Coverage
# ✅ Script Optimization %
# ✅ Cache Header Analysis
# ✅ Mobile Responsiveness
# ✅ CLS Detection
# ✅ Image Optimization %
# ✅ Third-party Script Analysis
# ✅ CDN Detection
# ✅ Monitoring Tool Detection
# ✅ Analytics Detection
# ✅ Real Evidence-Based Compliance
# ✅ DOCX Report
# ✅ Screenshot Proofs
# ✅ Structured Metric Tables
#
# =========================================================
# INSTALL
# =========================================================
#
# pip install playwright pillow python-docx
# pip install beautifulsoup4 lxml
#
# playwright install
#
# =========================================================

import asyncio
import os
import time

from collections import defaultdict
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from bs4 import BeautifulSoup

from PIL import Image
from PIL import ImageDraw

from docx import Document
from docx.shared import Inches

# =========================================================
# FOLDERS
# =========================================================

folders = [

    "screenshots",
    "annotated",
    "reports"

]

for folder in folders:

    os.makedirs(folder, exist_ok=True)

# =========================================================
# STORAGE
# =========================================================

results = []

network_responses = []

network_resources = []

# =========================================================
# EVIDENCE
# =========================================================

def add_evidence(

    section,
    title,
    status,
    reason,
    metrics,
    screenshot=None

):

    results.append({

        "section": section,
        "title": title,
        "status": status,
        "reason": reason,
        "metrics": metrics,
        "screenshot": screenshot

    })

# =========================================================
# ANNOTATE
# =========================================================

def annotate(

    image_path,
    output_path,
    x,
    y,
    w,
    h,
    text,
    compliant=True

):

    image = Image.open(image_path)

    draw = ImageDraw.Draw(image)

    color = "green" if compliant else "red"

    draw.rectangle(

        [

            (x,y),
            (x+w,y+h)

        ],

        outline=color,
        width=6

    )

    draw.rectangle(

        [

            (x,y-50),
            (x+750,y-10)

        ],

        fill=color

    )

    draw.text(

        (x+10,y-42),

        text,

        fill="white"

    )

    image.save(output_path)

    return output_path

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

async def safe_ss(page, path):

    try:

        await page.screenshot(

            path=path,
            full_page=True

        )

    except:
        pass

def hostname(value):

    try:

        return urlparse(value).hostname or ""

    except:

        return ""

def same_site(url_a, url_b):

    host_a = hostname(url_a)
    host_b = hostname(url_b)

    if not host_a or not host_b:
        return True

    return (
        host_a == host_b
        or host_a.endswith("." + host_b)
        or host_b.endswith("." + host_a)
    )

def unique_sorted(values):

    return sorted(
        set(v for v in values if v)
    )

# =========================================================
# PAGE SPEED
# =========================================================

async def test_page_speed(page):

    print("\nTESTING 10.1.1")

    metrics = await page.evaluate(

        """
        () => {

            const nav = performance.getEntriesByType("navigation")[0];

            if (nav) {

                return {

                    ttfb: Math.round(nav.responseStart),
                    dom: Math.round(nav.domContentLoadedEventEnd),
                    load: Math.round(nav.loadEventEnd),
                    transfer: Math.round(nav.transferSize || 0),
                    encoded: Math.round(nav.encodedBodySize || 0)

                };

            }

            const t = performance.timing;

            return {

                ttfb: t.responseStart - t.navigationStart,
                dom: t.domContentLoadedEventEnd - t.navigationStart,
                load: t.loadEventEnd - t.navigationStart,
                transfer: 0,
                encoded: 0

            };

        }
        """

    )

    ttfb = max(0, metrics["ttfb"])
    dom_load = max(0, metrics["dom"])
    full_load = max(0, metrics["load"])

    compliant = (
        ttfb <= 800
        and dom_load <= 2500
        and full_load <= 4000
    )

    ss = "screenshots/page_speed.png"

    await safe_ss(page, ss)

    ann = annotate(

        ss,

        "annotated/page_speed.png",

        40,
        40,
        700,
        140,

        f"TTFB:{ttfb}ms | "
        f"DOM:{dom_load}ms | "
        f"LOAD:{full_load}ms",

        compliant

    )

    metrics_table = {

        "TTFB": f"{ttfb} ms",
        "DOM Load": f"{dom_load} ms",
        "Full Load": f"{full_load} ms",
        "Transfer Size": f"{metrics['transfer']} bytes",
        "Encoded Body": f"{metrics['encoded']} bytes"

    }

    if compliant:

        reason = (

            "Website loading performance "
            "is within DBIM threshold."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Website loading speed exceeds "
            "recommended DBIM threshold."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.1.1",

        "Page Loading Speed",

        status,

        reason,

        metrics_table,

        ann

    )

# =========================================================
# LAZY LOADING
# =========================================================

async def test_lazy_loading(page):

    print("\nTESTING 10.1.2")

    image_metrics = await page.evaluate(

        """
        () => Array.from(document.images).map(img => {

            const rect = img.getBoundingClientRect();
            const top = rect.top + window.scrollY;
            const belowFold = top > window.innerHeight;

            return {

                loading: (img.getAttribute("loading") || "").toLowerCase(),
                belowFold,
                visible: rect.width > 0 && rect.height > 0

            };

        })
        """

    )

    images = [
        img for img in image_metrics
        if img["visible"]
    ]

    lazy_candidates = [
        img for img in images
        if img["belowFold"]
    ]

    total = len(lazy_candidates)

    lazy = sum(
        1 for img in lazy_candidates
        if img["loading"] == "lazy"
    )

    coverage = 0

    if total > 0:

        coverage = round(

            (lazy/total)*100,
            2

        )

    compliant = total == 0 or coverage >= 70

    metrics_table = {

        "Visible Images": len(images),
        "Below-fold Images": total,
        "Lazy-loaded Below-fold Images": lazy,
        "Coverage": f"{coverage}%"

    }

    if compliant:

        reason = (

            "Lazy loading coverage is sufficient."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Insufficient lazy loading coverage."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.1.2",

        "Lazy Loading",

        status,

        reason,

        metrics_table

    )

# =========================================================
# CRITICAL RENDERING
# =========================================================

async def test_rendering(page):

    print("\nTESTING 10.1.3")

    html = await page.content()

    soup = BeautifulSoup(

        html,
        "lxml"

    )

    scripts = soup.find_all("script")

    total = len(scripts)

    async_count = 0
    defer_count = 0
    blocking = 0
    module_count = 0

    for s in scripts:

        script_type = (s.get("type") or "").lower()

        has_src = bool(s.get("src"))

        in_head = s.find_parent("head") is not None

        if script_type == "module":

            module_count += 1

        elif s.get("async") is not None:

            async_count += 1

        elif s.get("defer") is not None:

            defer_count += 1

        elif has_src and in_head:

            blocking += 1

    blocking_ratio = 0

    if total > 0:

        blocking_ratio = round(

            (blocking/total)*100,
            2

        )

    compliant = blocking_ratio <= 20

    metrics_table = {

        "Total Scripts": total,
        "Async": async_count,
        "Deferred": defer_count,
        "Modules": module_count,
        "Head Blocking External": blocking,
        "Blocking Ratio": f"{blocking_ratio}%"

    }

    if compliant:

        reason = (

            "Critical rendering path optimized."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Too many render-blocking scripts."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.1.3",

        "Critical Rendering Optimization",

        status,

        reason,

        metrics_table

    )

# =========================================================
# CACHE HEADERS
# =========================================================

async def test_cache():

    print("\nTESTING 10.1.4")

    cached = 0

    cacheable_types = {
        "stylesheet",
        "script",
        "image",
        "font"
    }

    resources = [
        r for r in network_resources
        if r["resource_type"] in cacheable_types
        and r["status"] < 400
    ]

    total = len(resources)

    for resource in resources:

        headers = resource["headers"]

        cc = headers.get(
            "cache-control",
            ""
        ).lower()

        etag = headers.get(
            "etag",
            ""
        )

        expires = headers.get(
            "expires",
            ""
        )

        if (

            "no-store" not in cc
            and
            (
            "max-age" in cc
            or
            etag
            or
            expires
            )

        ):

            cached += 1

    coverage = 0

    if total > 0:

        coverage = round(

            (cached/total)*100,
            2

        )

    compliant = total == 0 or coverage >= 70

    metrics_table = {

        "Resources": total,
        "Cached": cached,
        "Cache Coverage": f"{coverage}%"

    }

    if compliant:

        reason = (

            "Caching strategy implemented properly."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Insufficient caching headers detected."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.1.4",

        "Browser Caching",

        status,

        reason,

        metrics_table

    )

# =========================================================
# INTERACTION
# =========================================================

async def test_interaction(page):

    print("\nTESTING 10.2.1")

    responsiveness = await page.evaluate(

        """
        () => new Promise(resolve => {

            let maxLongTask = 0;
            let longTasks = 0;
            let supported = "PerformanceObserver" in window;

            if (!supported) {
                resolve({ supported:false, maxLongTask:0, longTasks:0 });
                return;
            }

            try {

                const observer = new PerformanceObserver(list => {

                    for (const entry of list.getEntries()) {

                        longTasks++;
                        maxLongTask = Math.max(maxLongTask, entry.duration);

                    }

                });

                observer.observe({ type:"longtask", buffered:true });

                window.dispatchEvent(new Event("scroll"));

                setTimeout(() => {

                    observer.disconnect();
                    resolve({
                        supported:true,
                        maxLongTask:Math.round(maxLongTask),
                        longTasks
                    });

                }, 1500);

            } catch (err) {

                resolve({ supported:false, maxLongTask:0, longTasks:0 });

            }

        })
        """

    )

    delay = responsiveness["maxLongTask"]

    compliant = (
        not responsiveness["supported"]
        or delay < 200
    )

    metrics_table = {

        "Max Long Task": f"{delay} ms",
        "Long Task Count": responsiveness["longTasks"],
        "Observer Supported": responsiveness["supported"]

    }

    if compliant:

        reason = (

            "Website interactions are responsive."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Website interactions are slow."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.2.1",

        "Interaction Responsiveness",

        status,

        reason,

        metrics_table

    )

# =========================================================
# MOBILE RESPONSIVENESS
# =========================================================

async def test_mobile(page, browser):

    print("\nTESTING 10.2.2")

    mobile = await browser.new_page(

        viewport={

            "width":390,
            "height":844

        }

    )

    await mobile.goto(page.url)

    await smart_wait(mobile, 5000)

    overflow = await mobile.evaluate(

        """
        () => {

            return {

                width:
                    Math.max(
                        document.body.scrollWidth,
                        document.documentElement.scrollWidth
                    ),

                viewport:
                    window.innerWidth

            };

        }
        """

    )

    page_width = overflow["width"]
    viewport = overflow["viewport"]

    compliant = page_width <= viewport + 2

    ss = "screenshots/mobile.png"

    await safe_ss(mobile, ss)

    ann = annotate(

        ss,

        "annotated/mobile.png",

        20,
        20,
        350,
        120,

        f"Page:{page_width}px | "
        f"Viewport:{viewport}px",

        compliant

    )

    metrics_table = {

        "Page Width": f"{page_width}px",
        "Viewport Width": f"{viewport}px",
        "Overflow": "NO" if compliant else "YES"

    }

    if compliant:

        reason = (

            "Website adapts correctly "
            "to mobile viewport."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Horizontal overflow detected "
            "on mobile."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.2.2",

        "Mobile Responsiveness",

        status,

        reason,

        metrics_table,

        ann

    )

    await mobile.close()

# =========================================================
# CLS
# =========================================================

async def test_cls(page):

    print("\nTESTING 10.3.1")

    cls = await page.evaluate(

        """
        () => {

            return new Promise(resolve => {

                let clsValue = 0;

                let shifts = 0;

                new PerformanceObserver(list => {

                    for (const entry of list.getEntries()) {

                        if (!entry.hadRecentInput) {

                            clsValue += entry.value;

                            shifts++;

                        }

                    }

                }).observe({

                    type:'layout-shift',
                    buffered:true

                });

                setTimeout(() => {

                    resolve({

                        cls: clsValue,
                        shifts: shifts

                    });

                },5000);

            });

        }
        """

    )

    score = round(
        cls["cls"],
        4
    )

    shifts = cls["shifts"]

    compliant = score < 0.1

    ss = "screenshots/cls.png"

    await safe_ss(page, ss)

    ann = annotate(

        ss,

        "annotated/cls.png",

        40,
        40,
        700,
        140,

        f"CLS:{score} | "
        f"Shifts:{shifts}",

        compliant

    )

    metrics_table = {

        "CLS Score": score,
        "Shift Events": shifts

    }

    if compliant:

        reason = (

            "Visual layout stability acceptable."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Unexpected layout shifts detected."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.3.1",

        "Visual Stability",

        status,

        reason,

        metrics_table,

        ann

    )

# =========================================================
# IMAGE OPTIMIZATION
# =========================================================

async def test_images(page):

    print("\nTESTING 10.3.2")

    image_metrics = await page.evaluate(

        """
        () => Array.from(document.images).map(img => {

            const src = (
                img.currentSrc
                || img.getAttribute("src")
                || img.getAttribute("data-src")
                || ""
            ).toLowerCase();

            const rect = img.getBoundingClientRect();

            return {

                src,
                width: rect.width,
                height: rect.height,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                visible: rect.width > 0 && rect.height > 0

            };

        })
        """

    )

    images = [
        img for img in image_metrics
        if img["visible"]
    ]

    total = len(images)

    webp = 0
    avif = 0
    oversized = 0

    for img in images:

        src = img["src"]

        if ".webp" in src:

            webp += 1

        elif ".avif" in src:

            avif += 1

        rendered_w = max(1, img["width"])
        rendered_h = max(1, img["height"])

        if (
            img["naturalWidth"] > rendered_w * 2.5
            or
            img["naturalHeight"] > rendered_h * 2.5
        ):

            oversized += 1

    optimized = webp + avif
    legacy = max(0, total - optimized)

    coverage = 0

    if total > 0:

        coverage = round(

            (optimized/total)*100,
            2

        )

    oversized_ratio = 0

    if total > 0:

        oversized_ratio = round(
            (oversized/total)*100,
            2
        )

    compliant = total == 0 or (
        coverage >= 40
        and oversized_ratio <= 30
    )

    metrics_table = {

        "Total": total,
        "WEBP": webp,
        "AVIF": avif,
        "Legacy": legacy,
        "Oversized Images": oversized,
        "Optimization Coverage": f"{coverage}%",
        "Oversized Ratio": f"{oversized_ratio}%"

    }

    if compliant:

        reason = (

            "Optimized image formats used."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Image optimization insufficient."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.3.2",

        "Image Optimization",

        status,

        reason,

        metrics_table

    )

# =========================================================
# THIRD PARTY
# =========================================================

async def test_scripts(page):

    print("\nTESTING 10.4.1")

    page_host = hostname(page.url)

    domains = set()

    for resource in network_resources:

        if resource["resource_type"] != "script":
            continue

        domain = hostname(resource["url"])

        if not same_site(resource["url"], page.url):

            domains.add(domain)

    count = len(domains)

    compliant = count <= 5

    metrics_table = {

        "Third-party Domains": "\n".join(unique_sorted(domains)),
        "Count": count

    }

    if compliant:

        reason = (

            "Limited third-party dependency."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "Too many third-party resources."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.4.1",

        "Third-party Script Minimization",

        status,

        reason,

        metrics_table

    )

# =========================================================
# CDN
# =========================================================

async def test_cdn(page):

    print("\nTESTING 10.4.2")

    html = (await page.content()).lower()

    cdns = set()

    keywords = {

        "cloudflare":"Cloudflare",
        "akamai":"Akamai",
        "jsdelivr":"jsDelivr",
        "cloudfront":"CloudFront",
        "fastly":"Fastly",
        "azureedge":"Azure CDN",
        "stackpath":"StackPath",
        "unpkg":"unpkg",
        "cdn":"Generic CDN"

    }

    evidence_text = html + " " + " ".join(
        resource["url"].lower()
        for resource in network_resources
    )

    for key, val in keywords.items():

        if key in evidence_text:

            cdns.add(val)

    cdns = unique_sorted(cdns)

    compliant = len(cdns) > 0

    metrics_table = {

        "Detected CDNs": "\n".join(cdns)
        if cdns else "None"

    }

    if compliant:

        reason = (

            "Content Delivery Network detected."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "No CDN usage detected."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.4.2",

        "CDN Usage",

        status,

        reason,

        metrics_table

    )

# =========================================================
# MONITORING
# =========================================================

async def test_monitoring(page):

    print("\nTESTING 10.4.3")

    html = (await page.content()).lower()

    evidence_text = html + " " + " ".join(
        resource["url"].lower()
        for resource in network_resources
    )

    tools = set()

    keywords = {

        "sentry":"Sentry",
        "newrelic":"NewRelic",
        "datadog":"Datadog",
        "dynatrace":"Dynatrace",
        "appdynamics":"AppDynamics",
        "speedcurve":"SpeedCurve",
        "raygun":"Raygun",
        "boomerang":"Boomerang"

    }

    for key,val in keywords.items():

        if key in evidence_text:

            tools.add(val)

    tools = unique_sorted(tools)

    compliant = len(tools) > 0

    metrics_table = {

        "Monitoring Tools":
            "\n".join(tools)
            if tools else "None"

    }

    if compliant:

        reason = (

            "Performance monitoring tools detected."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "No monitoring tools detected."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.4.3",

        "Performance Monitoring",

        status,

        reason,

        metrics_table

    )

# =========================================================
# ANALYTICS
# =========================================================

async def test_analytics(page):

    print("\nTESTING 10.5")

    html = (await page.content()).lower()

    evidence_text = html + " " + " ".join(
        resource["url"].lower()
        for resource in network_resources
    )

    tools = set()

    analytics = {

        "google-analytics":"Google Analytics",
        "googletagmanager":"GTM",
        "gtag":"gtag.js",
        "matomo":"Matomo",
        "plausible":"Plausible",
        "hotjar":"Hotjar",
        "clarity.ms":"Microsoft Clarity",
        "segment.io":"Segment",
        "mixpanel":"Mixpanel"

    }

    for key,val in analytics.items():

        if key in evidence_text:

            tools.add(val)

    tools = unique_sorted(tools)

    compliant = len(tools) > 0

    metrics_table = {

        "Analytics Platforms":
            "\n".join(tools)
            if tools else "None"

    }

    if compliant:

        reason = (

            "Analytics integration detected."

        )

        status = "COMPLIANT"

    else:

        reason = (

            "No analytics integration detected."

        )

        status = "NON-COMPLIANT"

    add_evidence(

        "10.5",

        "Analytics Integration",

        status,

        reason,

        metrics_table

    )

# =========================================================
# REPORT
# =========================================================

def generate_report():

    doc = Document()

    doc.add_heading(

        "DBIM PERFORMANCE ENHANCEMENT REPORT",

        level=1

    )

    for r in results:

        doc.add_heading(

            f"{r['section']} - {r['title']}",

            level=2

        )

        doc.add_paragraph(

            f"STATUS: {r['status']}"

        )

        doc.add_paragraph(

            r["reason"]

        )

        # =============================================
        # METRICS TABLE
        # =============================================

        table = doc.add_table(

            rows=1,
            cols=2

        )

        hdr = table.rows[0].cells

        hdr[0].text = "Metric"
        hdr[1].text = "Value"

        for k,v in r["metrics"].items():

            row = table.add_row().cells

            row[0].text = str(k)
            row[1].text = str(v)

        # =============================================
        # SCREENSHOT
        # =============================================

        if r["screenshot"]:

            doc.add_picture(

                r["screenshot"],

                width=Inches(6)

            )

    doc.save(

        "reports/performance_report.docx"

    )

# =========================================================
# MAIN
# =========================================================

async def performance_engine():

    url = input(

        "\nEnter Website URL: "

    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(

            headless=os.getenv("DBIM_HEADED") != "1"

        )

        page = await browser.new_page(

            viewport={

                "width":1440,
                "height":900

            }

        )

        # =============================================
        # RESPONSE TRACKING
        # =============================================

        def track_response(response):

            resource = {

                "url": response.url,
                "status": response.status,
                "headers": response.headers,
                "resource_type": response.request.resource_type

            }

            network_resources.append(resource)

            network_responses.append(response.headers)

        page.on(

            "response",

            track_response

        )

        print("\nOPENING WEBSITE...")

        await page.goto(

            url,

            wait_until="domcontentloaded"

        )

        await smart_wait(page, 6000)

        print("\nUPDATED: WEBSITE OPENED")

        # =============================================
        # TESTS
        # =============================================

        await test_page_speed(page)

        await test_lazy_loading(page)

        await test_rendering(page)

        await test_cache()

        await test_interaction(page)

        await test_mobile(page, browser)

        await test_cls(page)

        await test_images(page)

        await test_scripts(page)

        await test_cdn(page)

        await test_monitoring(page)

        await test_analytics(page)

        await browser.close()

    # =============================================
    # REPORT
    # =============================================

    generate_report()

    print("\nFINAL REPORT GENERATED")

# =========================================================
# RUN
# =========================================================

asyncio.run(

    performance_engine()

)
