import csv
import time
import os
import sys
import requests

SUBREDDITS = [
    "Jokes", "3amjokes", "DadJokes", "CleanJokes", "Puns",
    "Oneliners", "AntiJokes", "BadJokes", "copypasta",
    "bookscirclejerk", "moviescirclejerk", "Gamingcirclejerk",
    "soccercirclejerk", "nbacirclejerk", "memes", "okbuddycinephile", 
    "okbuddyretard", "shitposting", "anarchychess", "whenthe",
    "sillyconfession", "dankchristianmemes", "shittymoviedetails", "funny",
    "TIFU", "Unexpected", "ComedyCemetery", "dankmemes",  "CrappyDesign", 
    "AnimalsBeingDerps", "wholesomememes", "me_irl", "gifs", "BlursedImages",
    "Blursedcomments", "comedyheaven", "cringepics", "cringe", "PeopleFuckingDying",
    "perfectlycutscreams", "raimimemes", "shid_and_camed", "wtfstockphotos", "youngpeopleyoutube", 
    "MoldyMemes", "nukedmemes", "tombstoning", "fatsquirrelhate", "engrish", "guitarcirclejerk", "vinuljerk", 
    "childrenfallingover", "ContagiousLaughter", "SipsTea", "wallstreetbets", "astrologymemes",
    "funnyanimals", "funnycats", "funnyvideos"
]
POSTS_PER_SUB = 70  # adjust to reach ~1 000 posts
HEADERS = {"User-Agent": "reddit-humor-scraper/0.1"}

def extract_image_url(post):
    # gallery posts
    if post.get("is_gallery"):
        gallery = post.get("gallery_data", {}).get("items", [])
        media_metadata = post.get("media_metadata", {})
        if gallery and media_metadata:
            first = gallery[0]
            info = media_metadata.get(first["media_id"], {})
            if "s" in info and "u" in info["s"]:
                return info["s"]["u"].replace("&amp;", "&")
    # reddit hosted video
    media = post.get("secure_media") or post.get("media")
    if media and isinstance(media, dict):
        reddit_video = media.get("reddit_video")
        if reddit_video and isinstance(reddit_video, dict):
            dash = reddit_video.get("dash_url")
            fallback = reddit_video.get("fallback_url")
            if fallback:
                return fallback
            if dash:
                return dash

    # simple images
    url = post.get("url_overridden_by_dest") or post.get("url")
    if post.get("post_hint") == "image" and url:
        if url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            return url
    # preview fallback
    preview = post.get("preview", {})
    if "images" in preview:
        src_url = preview["images"][0]["source"]["url"].replace("&amp;", "&")
        if "external-preview.redd.it" in src_url:
            return ""  # skip external preview placeholders
        return src_url
    return ""

def fetch_posts(sub, limit):
    url = f"https://api.reddit.com/r/{sub}/hot?limit={limit}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()["data"]["children"]
    return [item["data"] for item in data]

def ensure_headers(text_path, image_path):
    if not os.path.exists(text_path) or os.path.getsize(text_path) == 0:
        with open(text_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["title", "text", "score", "subreddit"])
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        with open(image_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["title", "text", "score", "subreddit", "image_url"])


def cleanup_image_csv(image_path: str) -> tuple[int, int]:
    tmp_image_path = image_path + ".tmp"
    removed = 0
    kept = 0
    try:
        with open(image_path, "r", encoding="utf-8", newline="") as fin, \
             open(tmp_image_path, "w", encoding="utf-8", newline="") as fout:
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                url = (row.get("image_url") or "")
                if "external-preview.redd.it" in url:
                    removed += 1
                    continue
                writer.writerow(row)
                kept += 1
        os.replace(tmp_image_path, image_path)
    except Exception:
        try:
            if os.path.exists(tmp_image_path):
                os.remove(tmp_image_path)
        except Exception:
            pass
        raise
    return removed, kept


def main():
    base_dir = os.path.dirname(__file__)
    text_path = os.path.join(base_dir, "humor_text_posts.csv")
    image_path = os.path.join(base_dir, "humor_image_posts.csv")

    ensure_headers(text_path, image_path)

    # Cleanup-only mode: just purge external-preview rows and exit
    if "--clean" in sys.argv or os.environ.get("CLEAN_ONLY") == "1":
        try:
            removed, kept = cleanup_image_csv(image_path)
            print(f"Cleanup-only: removed {removed} external-preview rows, kept {kept}")
        except Exception as e:
            print(f"Cleanup-only failed: {e}")
        return

    for sub in SUBREDDITS:
        try:
            posts = fetch_posts(sub, limit=100)
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 403:
                print(f"403 Forbidden for r/{sub}, skipping…")
                time.sleep(0.3)
                continue
            print(f"HTTP error for r/{sub}: {e}. Skipping…")
            time.sleep(0.3)
            continue
        except requests.RequestException as e:
            print(f"Request failed for r/{sub}: {e}. Skipping…")
            time.sleep(0.3)
            continue

        text_count, img_count = 0, 0

        for p in posts:
            if p.get("stickied") or p.get("is_created_from_ads_ui"):
                continue
            title = p.get("title", "").strip()
            body = p.get("selftext", "").strip()
            score = p.get("score", 0)
            sr = p.get("subreddit", sub)
            img_url = extract_image_url(p)

            if img_url and img_count < POSTS_PER_SUB and "external-preview.redd.it" not in img_url:
                # Append image row immediately
                with open(image_path, "a", newline="", encoding="utf-8") as fimg:
                    csv.writer(fimg).writerow((title, body, score, sr, img_url))
                img_count += 1
            elif (title or body) and text_count < POSTS_PER_SUB:
                # Append text row immediately
                with open(text_path, "a", newline="", encoding="utf-8") as ftxt:
                    csv.writer(ftxt).writerow((title, body, score, sr))
                text_count += 1

            if text_count >= POSTS_PER_SUB and img_count >= POSTS_PER_SUB:
                break

        time.sleep(0.5)  # polite delay between subreddits

    # Cleanup pass after scraping
    try:
        removed, kept = cleanup_image_csv(image_path)
        if removed:
            print(f"Cleanup: removed {removed} external-preview rows, kept {kept}")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    main()
