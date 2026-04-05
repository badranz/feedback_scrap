from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import os
import sys

OUTPUT_DIR = "output"
HEADLESS = False
PAGE_WAIT_MS = 3000
POST_WAIT_MS = 2000

TARGETS = {
    "reports": {
        "enabled": False,
        "base_url": "https://features.salla.sa",
        "start_url": "https://features.salla.sa/ideas/?category=6996641039416789766",
        "output_file": os.path.join(OUTPUT_DIR, "reports_feedback.md"),
        "card_selector": ".idea.ideas__row",
        "link_selector": ".idea-link",
        "vote_count_selector": "span.vote-count",
        "pagination_selector": ".pagination",
        "active_page_selector": "li.active",
        "next_page_selector": 'a[aria-label="Next page"]',
        "last_page_selector": 'a[aria-label="Last page"]',
        "description_selector": ".idea-content__description",
    },
    "placeholder_example": {
        "enabled": False,
        "base_url": "https://example.com",
        "start_url": "https://example.com/ideas/?category=REPLACE_ME",
        "output_file": os.path.join(OUTPUT_DIR, "placeholder_feedback.md"),
        "card_selector": ".idea.ideas__row",
        "link_selector": ".idea-link",
        "vote_count_selector": "span.vote-count",
        "pagination_selector": ".pagination",
        "active_page_selector": "li.active",
        "next_page_selector": 'a[aria-label="Next page"]',
        "last_page_selector": 'a[aria-label="Last page"]',
        "description_selector": ".idea-content__description",
    },
     "customers": {
        "enabled": True,
        "base_url": "https://features.salla.sa",
        "start_url": "https://features.salla.sa/ideas/?category=7038919660098458485",
        "output_file": os.path.join(OUTPUT_DIR, "customers_feedback.md"),
        "card_selector": ".idea.ideas__row",
        "link_selector": ".idea-link",
        "vote_count_selector": "span.vote-count",
        "pagination_selector": ".pagination",
        "active_page_selector": "li.active",
        "next_page_selector": 'a[aria-label="Next page"]',
        "last_page_selector": 'a[aria-label="Last page"]',
        "description_selector": ".idea-content__description",
    },
}


def get_enabled_targets() -> list[tuple[str, dict]]:
    enabled_targets = []
    for name, target in TARGETS.items():
        if target.get("enabled"):
            enabled_targets.append((name, target))
    return enabled_targets



def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())



def safe_inner_text(locator) -> str:
    try:
        if locator.count() > 0:
            return clean_text(locator.first.inner_text())
    except Exception:
        pass
    return ""



def safe_get_attr(locator, attr: str) -> str:
    try:
        if locator.count() > 0:
            return locator.first.get_attribute(attr) or ""
    except Exception:
        pass
    return ""



def extract_page_number_from_url(url: str) -> int:
    if not url:
        return 1

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    page_values = query.get("page", [])

    if not page_values:
        return 1

    try:
        return int(page_values[0])
    except (TypeError, ValueError):
        return 1



def build_page_url(page_number: int, target: dict) -> str:
    parsed = urlparse(target["start_url"])
    query = parse_qs(parsed.query)

    if page_number <= 1:
        query.pop("page", None)
    else:
        query["page"] = [str(page_number)]

    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))



def get_total_pages(page, target: dict) -> int:
    pagination = page.locator(target["pagination_selector"])
    if pagination.count() == 0:
        print("Debug: pagination not found, defaulting to 1 page")
        return 1

    last_link = pagination.locator(target["last_page_selector"])
    last_href = safe_get_attr(last_link, "href")
    if last_href:
        total_pages = extract_page_number_from_url(urljoin(target["base_url"], last_href))
        print(f"Debug: total pages detected from Last page link = {total_pages}")
        return max(total_pages, 1)

    page_links = pagination.locator('a[aria-label^="Page "]')
    max_page = 1

    for i in range(page_links.count()):
        href = safe_get_attr(page_links.nth(i), "href")
        full = urljoin(target["base_url"], href) if href else ""
        max_page = max(max_page, extract_page_number_from_url(full))

    next_link = pagination.locator(target["next_page_selector"])
    next_href = safe_get_attr(next_link, "href")
    if next_href:
        next_page_num = extract_page_number_from_url(urljoin(target["base_url"], next_href))
        max_page = max(max_page, next_page_num)

    print(f"Debug: total pages detected from visible pagination fallback = {max_page}")
    return max_page



def collect_post_links(page, target: dict) -> list[str]:
    total_pages = get_total_pages(page, target)
    urls = []
    seen = set()

    for page_number in range(1, total_pages + 1):
        page_url = build_page_url(page_number, target)
        print(f"Debug: visiting board page {page_number}/{total_pages}: {page_url}")

        page.goto(page_url, wait_until="networkidle")
        page.wait_for_timeout(PAGE_WAIT_MS)

        active_page_text = safe_inner_text(page.locator(f"{target['active_page_selector']} a")) or safe_inner_text(page.locator(target["active_page_selector"]))
        print(f"Debug: active page text on loaded page = {active_page_text!r}")
        print(f"Debug: current page url = {page.url}")

        cards = page.locator(target["card_selector"])
        card_count = cards.count()
        print(f"Debug: found {card_count} idea cards on board page {page_number}")

        for i in range(card_count):
            card = cards.nth(i)
            link = card.locator(target["link_selector"])
            href = safe_get_attr(link, "href")
            title_text = safe_inner_text(link)

            if not href:
                continue

            full = urljoin(target["base_url"], href)
            if full in seen:
                continue

            seen.add(full)
            urls.append(full)
            print(f"Debug page {page_number} card {i + 1}: title='{title_text[:80]}' href='{full}'")

    print(f"Debug: collected {len(urls)} total post links from all pages")
    return urls



def extract_post(page, post_url: str, target: dict) -> dict:
    page.goto(post_url, wait_until="domcontentloaded")
    page.wait_for_timeout(POST_WAIT_MS)

    title_selectors = [
        "h1",
        target["link_selector"],
        '[data-testid="post-title"]',
        '[data-testid="post-name"]',
        'main h1',
        'article h1',
    ]

    description_selectors = [
        target["description_selector"],
        '[data-testid="post-content"]',
        '[data-testid="post-description"]',
        'article',
        'main',
        '[role="main"]',
    ]

    status_selectors = [
        '[data-testid="post-status"]',
        '[data-testid="status"]',
        'text=/planned|in progress|complete|under review|open|closed/i',
    ]

    vote_selectors = [
        target["vote_count_selector"],
        '[data-testid="vote-count"]',
        '[data-testid="votes"]',
        'button:has-text("vote")',
        'text=/^[0-9]+$/',
    ]

    comment_block_selectors = [
        '[data-testid="comment"]',
        '[data-testid="post-comment"]',
        'article [role="article"]',
        'main article',
        '[role="main"] article',
    ]

    title = ""
    for sel in title_selectors:
        title = safe_inner_text(page.locator(sel))
        if title:
            break

    description = ""
    for sel in description_selectors:
        description = safe_inner_text(page.locator(sel))
        if description and description != title:
            break

    status = ""
    for sel in status_selectors:
        status = safe_inner_text(page.locator(sel))
        if status:
            break

    votes = ""
    for sel in vote_selectors:
        votes = safe_inner_text(page.locator(sel))
        if votes:
            break

    comments = []
    comment_blocks = None

    for sel in comment_block_selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            comment_blocks = loc
            break

    if comment_blocks:
        for i in range(comment_blocks.count()):
            block = comment_blocks.nth(i)

            possible_author = safe_inner_text(block.locator("strong"))
            if not possible_author:
                possible_author = safe_inner_text(block.locator("h4"))
            if not possible_author:
                possible_author = safe_inner_text(block.locator("span"))

            text = safe_inner_text(block)

            if text and len(text) > 10:
                comments.append({
                    "author": possible_author,
                    "text": text,
                })

    print(f"Debug post: {post_url}")
    print(f"  title={title!r}")
    print(f"  status={status!r}")
    print(f"  votes={votes!r}")
    print(f"  comments={len(comments)}")

    return {
        "title": title,
        "description": description,
        "status": status,
        "votes": votes,
        "post_url": post_url,
        "comments": comments,
    }



def write_markdown(posts: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Canny Feedback Export\n\n")

        for idx, post in enumerate(posts, start=1):
            f.write(f"## Post {idx}\n")
            f.write(f"**Title:** {post.get('title', '')}  \n")
            f.write(f"**Status:** {post.get('status', '')}  \n")
            f.write(f"**Votes:** {post.get('votes', '')}  \n")
            f.write(f"**Post URL:** {post.get('post_url', '')}\n\n")

            f.write("**Description:**  \n")
            f.write(f"{post.get('description', '')}\n\n")

            f.write("### Comments\n")
            comments = post.get("comments", [])

            if not comments:
                f.write("_No comments found._\n\n")
                continue

            for c_idx, comment in enumerate(comments, start=1):
                f.write(f"#### Comment {c_idx}\n")
                f.write(f"- author: {comment.get('author', '')}\n")
                f.write(f"- text: {comment.get('text', '')}\n\n")



def run_target(name: str, target: dict) -> None:
    print(f"Starting target: {name}")
    posts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        page.goto(target["start_url"], wait_until="networkidle")
        page.wait_for_timeout(PAGE_WAIT_MS)
        post_links = collect_post_links(page, target)

        if not post_links:
            print("Debug: no post links found. Check target selectors and URL settings.")

        print(f"Found {len(post_links)} post links for target: {name}")

        for i, link in enumerate(post_links, start=1):
            try:
                post = extract_post(page, link, target)
                if post.get("title"):
                    posts.append(post)
                    print(f"[{i}/{len(post_links)}] saved: {link}")
                else:
                    print(f"[{i}/{len(post_links)}] skipped, no title found: {link}")
            except PlaywrightTimeoutError:
                print(f"[{i}/{len(post_links)}] timeout: {link}")
            except Exception as e:
                print(f"[{i}/{len(post_links)}] failed: {link} | {e}")

        browser.close()

    write_markdown(posts, target["output_file"])
    print(f"Saved {len(posts)} posts to {target['output_file']}")



def main():
    args = sys.argv[1:]
    enabled_targets = dict(get_enabled_targets())

    if args:
        target_name = args[0]

        if target_name not in TARGETS:
            available = ", ".join(TARGETS.keys())
            raise ValueError(f"Unknown target '{target_name}'. Available: {available}")

        target = TARGETS[target_name]
        run_target(target_name, target)
        return

    if not enabled_targets:
        raise ValueError("No enabled targets found. Set enabled=True for at least one target.")

    for name, target in enabled_targets.items():
        run_target(name, target)


if __name__ == "__main__":
    main()