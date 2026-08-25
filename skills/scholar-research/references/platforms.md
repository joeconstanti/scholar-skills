# Platform playbook

Use only the sections relevant to the requested run. Interfaces and access rules change; inspect the live product before relying on a query syntax.

## X / Twitter

Search core phrases, variants, hashtags, named accounts, and quoted links. Separate original posts from replies and reposts. Capture visible timestamps and metrics at observation time. Treat repost networks and screenshots without direct sources cautiously.

## LinkedIn

Search posts, newsletters, people, and company pages through available public or authenticated UI. Professional commentary is useful for role and industry language, but visible engagement is strongly network-dependent. Do not automate connection requests or collect non-public profile data.

## Facebook and Instagram

Prefer public pages, public groups, hashtags, Reels, and user-provided authenticated sessions. Record whether an item is paid or sponsored when visible. Private groups, profiles, and stories are out of scope unless the user supplies authorized exports.

## Google Search

Use date filters and diverse query formulations for discovery, then cite the underlying pages rather than the result page. Sample beyond the first few results and note localization or personalization. Compare recent results with an older baseline when claiming growth.

## Reddit

Search relevant communities as well as site-wide results. Capture post score and comment count separately, inspect high-signal comments, and distinguish a repeated community joke from broader demand. Use canonical post URLs and avoid treating votes as representative polling.

## ChatGPT Search and Perplexity

Use them for query expansion, discovery, and identifying sources. Open and evaluate their cited originals. Do not cite generated summaries as independent corroboration or count multiple answer engines citing the same page as breadth.

## TikTok

Search phrases, hashtags, sounds, creators, and comments through the available UI. Capture view/like/comment/share values only when visible and timestamp the observation. A sound or format can trend independently of the claim carried by a video.

## YouTube

Search videos, Shorts, channels, transcripts, and comments. Record publication time, views, and comments when visible. Normalize neither views nor subscriber counts across formats; compare like with like and inspect source links in descriptions.

## Collection engines

Use ordinary browser or HTTP tools first. For public pages at larger scale:

- Scrapling suits extraction that may need adaptive selectors, browser-backed fetching, or resumable spiders.
- Crawl4AI suits asynchronous browser crawling and Markdown-oriented extraction for downstream analysis.
- Scrapy suits durable, high-volume structured spiders with explicit pipelines and throttling.

Install optional tools in an isolated environment and pin versions for repeatable runs. Start with one page, validate output and permission boundaries, then scale conservatively. A crawler being technically capable of fetching a page does not make collection permitted.
