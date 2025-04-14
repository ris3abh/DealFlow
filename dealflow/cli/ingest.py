#!/usr/bin/env python
"""
ingest.py - CLI tool to perform dynamic ingestion of product knowledge using Firecrawl.
"""

import argparse
from dealflow.knowledge_base.crawler_ingestor import ingest_and_save

def main():
    parser = argparse.ArgumentParser(description="Ingest product information from a client website via Firecrawl")
    parser.add_argument("--url", required=True, help="Domain URL to crawl (e.g., https://example.com)")
    parser.add_argument("--cache", default="client_cache/entities.json", help="Path to cache file")
    args = parser.parse_args()

    entities = ingest_and_save(args.url, args.cache)
    print(f"Ingested {len(entities)} entities and saved to {args.cache}")

if __name__ == "__main__":
    main()
