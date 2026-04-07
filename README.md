## Overview

This tool scrapes feedback from Canny-style boards and exports it into structured Markdown files.

---

## Requirements

- macOS
- Python 3.10+
- Internet connection
- Playwright (installed via script)

---

## Installation

Run:

```bash
chmod +x install.sh
./install.sh
```

Then activate the environment:

```bash
source .venv/bin/activate
```

---

## Usage

### Run all enabled targets

```bash
python scrap_feedback.py
```

### Run a specific target

```bash
python scrap_feedback.py reports
```

---

## Output

- Output files are saved in:

```bash
output/
```

- Format: Markdown (`.md`)
- Each file contains:
  - Title
  - Status
  - Votes
  - Description
  - Comments

---

## Configure Targets

Targets are defined inside:

```bash
scrap_feedback.py
```

Each target controls:
- URL
- Selectors
- Output file

---

## Add a New Target

Add inside `TARGETS`:

```python
"my_target": {
    "enabled": True,
    "base_url": "https://your-domain.com",
    "start_url": "https://your-domain.com/ideas/?category=YOUR_CATEGORY_ID",
    "output_file": os.path.join(OUTPUT_DIR, "my_target_feedback.md"),

    "card_selector": ".idea.ideas__row",
    "link_selector": ".idea-link",
    "vote_count_selector": "span.vote-count",

    "pagination_selector": ".pagination",
    "active_page_selector": "li.active",
    "next_page_selector": 'a[aria-label="Next page"]',
    "last_page_selector": 'a[aria-label="Last page"]',

    "description_selector": ".idea-content__description",
}
```

---

## Enable / Disable Target

```python
"enabled": True   # run
"enabled": False  # ignore
```

---

## Debugging

To see browser while scraping:

```python
HEADLESS = False
```

To run silently:

```python
HEADLESS = True
```

---

## Notes

- Selectors may differ per website
- Use browser DevTools to inspect elements
- Pagination must exist or script defaults to 1 page

---

## Example Targets

- `reports` → working example
- `placeholder_example` → template

---

## Common Issues

### No data extracted
- Wrong selectors
- Wrong URL
- Page requires login

### Stops early in pagination
- Incorrect pagination selectors
- Site uses infinite scroll (not supported)
