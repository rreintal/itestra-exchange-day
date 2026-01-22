#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Dict, Any

import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm
from result import Result, Restaurant, Meal


BASE_URL = "https://www.paevapraad.ee/tallinn/nomme/"
TARGET_NAMES = {"Hiiu Pubi", "KIUS Restoran", "Jah Kallis Restoran"}
OUTPUT_CSV = Path("paevapraad_nomme.csv")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}
TIMEOUT = 15  # seconds

def fetch_page(url: str) -> str:
    """GET the page, raise on HTTP errors."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        sys.exit(f"❌ Could not download {url!r}: {exc}")


def text_or_none(tag: Tag) -> str | None:
    """Return stripped text or None if the tag is falsy."""
    return tag.get_text(strip=True) if tag else None


def parse_price(price_str: str) -> float | None:
    """
    Convert a string like "4,50 €" or "8.30 €" → float.
    Returns None on failure (so the CSV stays clean).
    """
    if not price_str:
        return None
    # remove any non‑numeric characters except comma/dot
    cleaned = re.sub(r"[^\d,\.]", "", price_str.replace(",", "."))
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_menu_items(diner_div: Tag) -> List[Dict[str, Any]]:
    """
    Inside a <div class="diner"> the menu is repeated as blocks:

        <div class="row full-view">
            <div class="text-right price "><span>4,50 €</span></div>
            <div class="food"><span>Borš</span></div>
        </div>

    This helper returns a list like:
        [{"dish": "Borš", "price": 4.5}, ...]
    """
    menu = {}
    for row in diner_div.select("div.row.full-view"):
        price_tag = row.select_one("div.price span")
        dish_tag = row.select_one("div.food span")
        price = parse_price(text_or_none(price_tag))
        dish = text_or_none(dish_tag)
        if dish and dish not in menu:
            # store the whole dict so later we can dump it as JSON
            menu[dish] = {"dish": dish, "price": price}
    return list(menu.values())


def parse_one_diner(diner_div: Tag) -> Dict[str, Any]:
    """
    Extract all fields we care about from a single `<div class="diner">` block.
    """
    name = diner_div.get("data-name") or text_or_none(diner_div.select_one("h2"))
    if not name:
        return {}

    # Opening hours / description – the span with class `lunchtime`
    schedule = text_or_none(diner_div.select_one("span.lunchtime"))

    menu = extract_menu_items(diner_div)

    return {
        "name": name,
        "schedule": schedule,
        "menu": json.dumps(menu, ensure_ascii=False),  # store as JSON string in CSV
    }


def scrape_page(html: str) -> Dict[str, Any]:
    """Parse the whole page and return a dict of restaurant dictionaries."""
    soup = BeautifulSoup(html, "lxml")
    diners = soup.select("div.diner")
    results = {}
    for diner in diners:
        data = parse_one_diner(diner)
        if not data:
            continue
        if data["name"] in TARGET_NAMES:
            results[data["name"]] = data
    return results


def write_csv(records: List[Dict[str, Any]], path: Path) -> None:
    """Write a list of dicts to CSV, preserving column order."""
    if not records:
        print("⚠️ No records to write.")
        return

    fieldnames = [
        "name",
        "menu"
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Wrote {len(records)} rows → {path}")


def record_to_Result(records: Iterable[Dict[str, Any]]) -> str:

    lines: List[str] = []
    restaurants = []
    for rec in records:
        name = rec.get("name", "Unnamed")

        raw_menu = rec.get("menu", [])
        if isinstance(raw_menu, str):
            try:
                raw_menu = json.loads(raw_menu)
            except json.JSONDecodeError:
                raw_menu = []  # malformed JSON → empty menu

        for item in raw_menu:
            dish = item.get("dish", "").replace("|", r"\|")  # escape pipe chars
            price = item.get("price")

            Meal_obj = Meal(name=dish, price=price)
            restaurant = Restaurant(name=name, emoji="", meals=[Meal_obj])
            restaurants.insert(0, restaurant)
            
    restaurants = set(restaurants)
    result = Result(restaurants=restaurants)
    print("✅ Parsed Result object.")
    print(len(result.restaurants))
    #print(result.restaurants[0].name)
    
    return result


def scrape():
    html = fetch_page(BASE_URL)
    records = scrape_page(html)

    if not records:
        print("⚠️ No matching restaurants found – check TARGET_NAMES or page structure.")
        sys.exit(0)

    return record_to_Result(records.values())   # pass the dict‑values view
    
    

    
def getResult():
    return scrape()