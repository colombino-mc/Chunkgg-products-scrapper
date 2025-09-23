import html
import json
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import scrapy

from chunkgg.items import MarketplaceItem


CATEGORY_ORDER = [
    ("/mashups", "Mashups"),
    ("/add-ons", "Add-Ons"),
    ("/worlds", "Worlds"),
    ("/textures", "Textures"),
    ("/skins", "Skins"),
]
CATEGORY_PATHS = {path: label for path, label in CATEGORY_ORDER}


class ChunkMarketplaceSpider(scrapy.Spider):
    """Scrapes chunk.gg category listings and product detail pages."""

    name = "chunk_marketplace"
    allowed_domains = ["chunk.gg"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 0.4,
        "FEED_EXPORT_ENCODING": "utf-8-sig",
    }

    def __init__(self, max_pages: int = 50, categories: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = int(max_pages)
        self._seen_products = set()
        self._selected_paths = self._resolve_categories(categories)

    def _resolve_categories(self, categories: Optional[str]) -> List[str]:
        if not categories:
            return [path for path, _ in CATEGORY_ORDER]

        lookup = {}
        for path, label in CATEGORY_ORDER:
            lookup[path.strip("/").lower()] = path
            lookup[path.lower()] = path
            lookup[label.lower()] = path

        requested = [token.strip().lower() for token in str(categories).split(",") if token.strip()]
        selected: List[str] = []
        seen = set()
        for token in requested:
            path = lookup.get(token)
            if path and path not in seen:
                selected.append(path)
                seen.add(path)

        if not selected:
            valid = ", ".join(label for _, label in CATEGORY_ORDER)
            raise ValueError(f"No valid categories found in '{categories}'. Accepted values: {valid}")
        return selected

    def start_requests(self):
        base = "https://chunk.gg"
        for path in self._selected_paths:
            label = CATEGORY_PATHS[path]
            url = urljoin(base, path)
            yield scrapy.Request(
                url,
                callback=self.parse_category,
                cb_kwargs={"category": label, "path": path, "page": 1},
            )

    def parse_category(self, response, category: str, path: str, page: int):
        for anchor in response.css("section.product-grid a[href^='/@']"):
            href = anchor.attrib.get("href")
            if not href or href in self._seen_products:
                continue
            self._seen_products.add(href)
            yield response.follow(
                href,
                callback=self.parse_product,
                cb_kwargs={"category": category},
                priority=10,
            )

        if page >= self.max_pages:
            return

        next_href = response.css(".pagination a[rel='next']::attr(href)").get()
        if next_href:
            yield response.follow(
                next_href,
                callback=self.parse_category,
                cb_kwargs={"category": category, "path": path, "page": page + 1},
                priority=0,
            )

    def parse_product(self, response, category: str):
        item = MarketplaceItem()
        item["product_url"] = response.url
        slug_path = urlparse(response.url).path
        item["slug"] = slug_path
        item["category"] = category

        product_slug = None
        creator_slug = None
        if slug_path:
            parts = slug_path.strip("/").split("/")
            if parts:
                handle = parts[0]
                if handle.startswith("@"):
                    handle = handle[1:]
                creator_slug = handle or None
            if len(parts) >= 2:
                product_slug = parts[-1] or None
        if creator_slug:
            item["creator_slug"] = creator_slug
        if product_slug:
            item["product_slug"] = product_slug

        title = response.css("h1.product-title::text").get()
        item["title"] = title.strip() if title else None

        creator = response.xpath("//a[@rel='author']//text()[normalize-space()]").get()
        item["creator"] = creator.strip() if creator else None

        creator_url = response.css("a[rel='author']::attr(href)").get()
        if creator_url:
            item["creator_url"] = response.urljoin(creator_url)

        description = response.css("meta[name='description']::attr(content)").get()
        item["description"] = self._clean_text(description)

        item["tags"] = self._extract_tags(response)

        price_text = response.css(".product-intro__details label-text::text").get()
        item["price_minecoins"] = self._to_int(price_text)
        item["is_free"] = (
            item["price_minecoins"] == 0 if item["price_minecoins"] is not None else None
        )

        item["price_usd"] = self._extract_price_usd(response)
        item["price_eur"] = self._extract_price_eur(response)
        item["has_trailer"] = False

        rating_value = self._to_float(response.css(".rating__count p::text").get())
        if rating_value is not None:
            item["rating_value"] = rating_value

        rating_count = self._extract_rating_count(response)
        if rating_count is not None:
            item["rating_count"] = rating_count

        rating_fraction, rating_out_of = self._extract_rating_fraction(response)
        if rating_out_of is not None:
            item["rating_out_of"] = rating_out_of
        if rating_fraction is not None and "rating_value" not in item:
            item["rating_value"] = self._to_float(rating_fraction.split("/")[0])

        rating_breakdown = self._extract_rating_breakdown(response)
        if rating_breakdown:
            self._apply_rating_breakdown(item, rating_breakdown)
            item["rating_breakdown"] = json.dumps(rating_breakdown, ensure_ascii=False)

        item["downloads"] = self._extract_downloads(response)

        details = self._extract_product_details(response)
        for key, value in details.items():
            if isinstance(value, str):
                value = self._clean_text(value)
            if value is not None:
                item[key] = value

        changelog = self._extract_changelog(response)
        if changelog:
            item["changelog"] = changelog

        uuid = self._extract_uuid(response)
        if uuid:
            item["uuid"] = uuid

        badge_info = self._extract_badges(response)
        badge_labels_list = badge_info.get("badge_labels", [])
        badge_modifiers_list = badge_info.get("badge_modifiers", [])
        if badge_info.get("skin_count") is not None:
            item["skin_count"] = badge_info["skin_count"]
        if badge_info.get("player_range"):
            item["player_range"] = badge_info["player_range"]
        if badge_labels_list:
            item["badge_labels"] = self._clean_text(" | ".join(badge_labels_list))
        if badge_modifiers_list:
            item["badge_modifiers"] = self._clean_text(" | ".join(badge_modifiers_list))

        supports_single, supports_multi = self._derive_player_flags(
            badge_info.get("player_range"),
            badge_labels_list,
            badge_modifiers_list,
        )
        if supports_single is not None:
            item["supports_singleplayer"] = supports_single
        if supports_multi is not None:
            item["supports_multiplayer"] = supports_multi

        trailer_info = self._extract_trailer_info(response)
        if trailer_info:
            for key, value in trailer_info.items():
                item[key] = value

        item["gallery"] = self._extract_gallery(response, slug_path)

        yield item

    def _extract_tags(self, response) -> Optional[List[str]]:
        tags: List[str] = []
        for anchor in response.css("a[rel='tag']"):
            parts = anchor.css("label-text::text").getall() or anchor.css("::text").getall()
            text = " ".join(part.strip() for part in parts if part and part.strip())
            if not text:
                continue
            text = re.sub(r"\s+", " ", text)
            text = re.sub(r"\s*/\s*", " / ", text)
            text = text.strip(" /,")
            if text:
                tags.append(text)
        deduped = list(dict.fromkeys(tags))
        return deduped or None

    def _extract_price_usd(self, response) -> Optional[float]:
        text = " ".join(response.css(".product-raw-text ::text").getall())
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\$\s*\(USD\)", text)
        if match:
            return float(match.group(1))
        return None

    def _extract_price_eur(self, response) -> Optional[float]:
        text = " ".join(response.css(".product-raw-text ::text").getall())
        match = re.search(r"([0-9]+(?:[\.,][0-9]+)?)\s*(?:\u20ac|EUR|EURO|\?)\s*\(EURO\)", text, flags=re.I)
        if match:
            value = match.group(1).replace(",", ".")
            try:
                return float(value)
            except ValueError:
                return None
        return None

    def _extract_rating_count(self, response) -> Optional[int]:
        rating_card = response.css("card-frame.product-details__rating")
        if rating_card:
            text = rating_card.xpath(".//p[contains(.,'Total of')]/text()").get()
            if text:
                match = re.search(r"Total of\s+([0-9.,]+)", text)
                if match:
                    return self._to_int(match.group(1))
        fallback = "".join(response.css(".rating__numbers ::text").getall())
        if fallback:
            return self._to_int(fallback)
        return None

    def _extract_rating_fraction(self, response) -> Tuple[Optional[str], Optional[int]]:
        rating_card = response.css("card-frame.product-details__rating")
        if rating_card:
            text = rating_card.xpath(".//p[contains(text(),'/')]/text()").get()
            if text:
                cleaned = text.strip()
                match = re.search(r"/\s*([0-9]+)", cleaned)
                out_of = int(match.group(1)) if match else None
                return cleaned, out_of
        return None, None

    def _extract_rating_breakdown(self, response) -> List[dict]:
        breakdown: List[dict] = []
        for wrapper in response.css("card-frame.product-details__rating .rating-bar-wrapper"):
            star = self._to_int(wrapper.css(".rating-bar-placement::text").get())
            if star is None:
                continue
            count = self._to_int(wrapper.css("progress-frame::attr(value)").get())
            percent = self._to_int(wrapper.xpath(".//p[contains(.,'%')]/text()").get())
            entry = {"star": star}
            if count is not None:
                entry["count"] = count
            if percent is not None:
                entry["percent"] = percent
            breakdown.append(entry)
        return breakdown

    def _apply_rating_breakdown(self, item: MarketplaceItem, breakdown: List[dict]):
        star_map = {}
        for entry in breakdown:
            star = entry.get("star")
            if star is None:
                continue
            star_map[int(star)] = entry
        for star in (5, 4, 3, 2, 1):
            entry = star_map.get(star, {})
            item[f"rating_{star}_count"] = entry.get("count")
            item[f"rating_{star}_percent"] = entry.get("percent")

    def _extract_product_details(self, response) -> dict:
        details_card = response.css("card-frame.product-details__data")
        data = {
            "min_version": None,
            "launched": None,
            "launched_iso": None,
            "last_updated": None,
            "last_updated_iso": None,
        }
        if not details_card:
            return data

        min_text = details_card.xpath(".//p[contains(.,'Minimum Version')]/text()").get()
        if min_text:
            match = re.search(r"Minimum Version:\s*(.+)", min_text)
            if match:
                data["min_version"] = match.group(1).strip()

        times = details_card.css("time")
        if len(times) >= 1:
            data["launched"] = times[0].xpath("normalize-space(text())").get()
            data["launched_iso"] = times[0].attrib.get("datetime")
        if len(times) >= 2:
            data["last_updated"] = times[1].xpath("normalize-space(text())").get()
            data["last_updated_iso"] = times[1].attrib.get("datetime")

        return data

    def _extract_changelog(self, response) -> Optional[str]:
        block = response.css("card-frame.product-details__changelog .changelog")
        if not block:
            return None
        lines = [
            text.strip()
            for text in block.xpath(".//text()[normalize-space()]").getall()
            if text and text.strip()
        ]
        if lines:
            return self._clean_text(" | ".join(lines))
        return None

    def _extract_uuid(self, response) -> Optional[str]:
        text = " ".join(response.css(".product-raw-text ::text").getall())
        match = re.search(r"UID\s+for\s+this\s+product\s+is\s+([0-9a-fA-F-]{36})", text)
        if match:
            return match.group(1)
        return None

    
    
    def _extract_badges(self, response) -> dict:
        data = {"skin_count": None, "player_range": None, "badge_labels": [], "badge_modifiers": []}
        paragraphs = response.css(".product-intro__content .label-box__paragraph::text").getall()
        for raw in paragraphs:
            text = self._clean_text(raw)
            if not text:
                continue
            match_skin = re.match(r"(\d+)\s+Skins?", text, flags=re.I)
            if match_skin:
                data["skin_count"] = int(match_skin.group(1))
                continue
            match_players = re.match(r"For\s+([0-9\s\-\u2013to]+)\s+Players", text, flags=re.I)
            if match_players:
                player_text = match_players.group(1)
                player_text = player_text.replace("to", "-").replace("\u2013", "-")
                data["player_range"] = self._clean_text(player_text)
                continue
            if "(" in text and text.endswith(")"):
                base, _, modifier = text.partition("(")
                base = base.strip()
                modifier = modifier.rstrip(")").strip()
                if base:
                    data["badge_labels"].append(base)
                if modifier:
                    data["badge_modifiers"].append(modifier)
                continue
            data["badge_labels"].append(text)

        data["badge_labels"] = list(dict.fromkeys(data["badge_labels"]))
        data["badge_modifiers"] = list(dict.fromkeys(data["badge_modifiers"]))
        return data

    def _derive_player_flags(
        self,
        player_range: Optional[str],
        badge_labels: List[str],
        badge_modifiers: List[str],
    ) -> Tuple[Optional[bool], Optional[bool]]:
        single = None
        multi = None

        if player_range:
            numbers = [int(n) for n in re.findall(r"\d+", player_range)]
            if numbers:
                if 1 in numbers:
                    single = True
                if any(n > 1 for n in numbers):
                    multi = True
                elif single and multi is None:
                    multi = False

        tokens = [t.lower() for t in (badge_labels or []) + (badge_modifiers or [])]
        for token in tokens:
            if "single" in token and single is None:
                single = True
            if "multi" in token and multi is None:
                multi = True

        return single, multi

    def _extract_trailer_info(self, response) -> Optional[dict]:
        data_video = response.css("[data-video]")
        trailer_present = bool(data_video)
        iframe_src = data_video.css("iframe::attr(src)").get()
        trailer_url = html.unescape(iframe_src.strip()) if iframe_src else None
        if trailer_url:
            trailer_url = trailer_url.rstrip("&")

        views_block = response.xpath(
            "//label-frame[.//p[contains(.,\'Trailer Views\')]]//p[contains(@class,\'label-box__paragraph\')]/text()"
        ).get()
        likes_block = response.xpath(
            "//label-frame[.//p[contains(.,\'Trailer Likes\')]]//p[contains(@class,\'label-box__paragraph\')]/text()"
        ).get()

        views = self._to_int(views_block)
        likes = self._to_int(likes_block)

        if not trailer_present and trailer_url is None and views is None and likes is None:
            return None

        return {
            "has_trailer": trailer_present or trailer_url is not None or views is not None,
            "trailer_url": trailer_url,
            "trailer_views": views,
            "trailer_likes": likes,
        }

    def _extract_downloads(self, response) -> Optional[int]:
        text_blocks = " ".join(response.css(".product-raw-text ::text").getall())
        match = re.search(r"([0-9][0-9,\.]+)\s+downloads", text_blocks, flags=re.I)
        if match:
            value = match.group(1)
            return self._to_int(value)
        return None

    def _extract_gallery(self, response, slug: str) -> Optional[List[str]]:
        product_slug = (slug or "").strip("/").split("/")[-1].lower()
        candidates = response.css("main product-image picture img::attr(src)").getall()
        filtered: List[str] = []
        for candidate in candidates:
            if not candidate:
                continue
            candidate = candidate.strip()
            lower = candidate.lower()
            if product_slug and f"/{product_slug}/" not in lower:
                continue
            filtered.append(candidate)
        ordered = list(dict.fromkeys(filtered))
        if not ordered:
            og_image = response.css("meta[property=\"og:image\"]::attr(content)").get()
            if og_image:
                ordered = [og_image.strip()]
        return ordered or None

    def _apply_rating_breakdown(self, item: MarketplaceItem, breakdown: List[dict]):
        star_map = {}
        for entry in breakdown:
            star = entry.get("star")
            if star is None:
                continue
            star_map[int(star)] = entry
        for star in (5, 4, 3, 2, 1):
            entry = star_map.get(star, {})
            item[f"rating_{star}_count"] = entry.get("count")
            item[f"rating_{star}_percent"] = entry.get("percent")

    @staticmethod
    def _clean_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", value)
        return cleaned.strip()

    @staticmethod
    def _to_int(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        digits = re.sub(r"[^0-9]", "", value)
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None
