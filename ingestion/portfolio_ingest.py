"""
Portfolio ingestion — consume JSON export from portfolio tool.

The user has an existing tool that provides all portfolio content
as a JSON object. This module parses that JSON and embeds it.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

import structlog

from ingestion.embedder import embed_and_store

logger = structlog.get_logger()


async def ingest_portfolio(json_path: str | None = None, json_data: dict | None = None) -> int:
    """Ingest portfolio data from a JSON export.

    Accepts either a file path, a URL, or a pre-parsed JSON dict.
    Defaults to fetching from the live portfolio if no path is provided.
    """
    if json_data is None:
        if not json_path:
            json_path = "https://alex-jansen-portfolio.lovable.app/resume.json"
            
        try:
            if json_path.startswith("http://") or json_path.startswith("https://"):
                logger.info("portfolio.fetch_url", url=json_path)
                req = urllib.request.Request(json_path, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    raw = response.read().decode("utf-8")
                    json_data = json.loads(raw)
            else:
                logger.info("portfolio.read_file", path=json_path)
                raw = Path(json_path).read_text(encoding="utf-8")
                json_data = json.loads(raw)
        except Exception as e:
            logger.error("portfolio.load.error", error=str(e), path=json_path)
            # Try to load local fallback if URL failed
            if json_path.startswith("http"):
                logger.info("portfolio.fallback_local")
                fallback_path = "ingestion/alex-jansen-resume (4).json"
                if Path(fallback_path).exists():
                    raw = Path(fallback_path).read_text(encoding="utf-8")
                    json_data = json.loads(raw)

    if not json_data:
        logger.warning("portfolio.ingest.no_data")
        return 0

    total_chunks = 0

    # ── Bio & Identities ─────────────────────────────────────────
    bio = json_data.get("bio", [])
    if bio:
        bio_text = "\n\n".join(bio)
        idents = json_data.get("identities", [])
        if idents:
            bio_text = f"Identities: {', '.join(idents)}\n\n" + bio_text
            
        chunks = await embed_and_store(
            text=f"Bio and Background:\n{bio_text}",
            source="portfolio:bio",
            content_type="bio",
            tags=["portfolio", "about", "bio"],
        )
        total_chunks += chunks

    # ── Skills ──────────────────────────────────────────────────
    skills = json_data.get("skills", [])
    if skills:
        skills_text = f"Core Technical & Product Skills:\n{', '.join(skills)}"
        chunks = await embed_and_store(
            text=skills_text,
            source="portfolio:skills",
            content_type="skills",
            tags=["portfolio", "skills"],
        )
        total_chunks += chunks

    # ── Experience ──────────────────────────────────────────────
    experience = json_data.get("experience", [])
    for exp in experience:
        title = exp.get("title", "Unknown Role")
        role = exp.get("role", "")
        year = exp.get("year", "")
        
        parts = [f"Experience: {title} ({year})"]
        if role:
            parts.append(f"Role: {role}")
            
        manager = exp.get("manager", {})
        if manager:
            parts.append(f"Challenge: {manager.get('challenge', '')}")
            parts.append(f"Strategy: {manager.get('strategy', '')}")
            parts.append(f"Impact: {manager.get('impact', '')}")
            
        builder = exp.get("builder", {})
        if builder:
            parts.append(f"Tech Stack: {builder.get('stack', '')}")
            for detail in builder.get("details", []):
                parts.append(f"{detail.get('label', 'Detail')}: {detail.get('description', '')}")

        exp_text = "\n\n".join(parts)
        tags = ["portfolio", "experience"] + [s.strip() for s in builder.get("stack", "").split(",") if s.strip()]
        
        chunks = await embed_and_store(
            text=exp_text,
            source=f"portfolio:experience:{exp.get('id', title)}",
            content_type="experience",
            tags=tags,
        )
        total_chunks += chunks

    # ── Labs / Projects ──────────────────────────────────────────
    labs = json_data.get("labs", [])
    for lab in labs:
        title = lab.get("title", "Unknown Project")
        parts = [
            f"Project: {title}",
            f"Description: {lab.get('description', '')}",
            f"Status: {lab.get('status', 'unknown')}"
        ]
        
        if lab.get("tech"):
            parts.append(f"Tech Stack: {', '.join(lab['tech'])}")
        
        for key in ["role", "timeline", "aiEngine", "buildersLog", "readme", "research"]:
            if val := lab.get(key):
                parts.append(f"{key.capitalize()}: {val}")
                
        lab_text = "\n\n".join(parts)
        tags = ["portfolio", "project", "lab"] + lab.get('tech', [])
        
        chunks = await embed_and_store(
            text=lab_text,
            source=f"portfolio:lab:{lab.get('id', title)}",
            content_type="project",
            tags=tags,
        )
        total_chunks += chunks
        
    # ── Publications ─────────────────────────────────────────────
    pubs = json_data.get("publications", [])
    for pub in pubs:
        title = pub.get("title", "Untitled")
        pub_text = f"Publication: {title}\nVenue: {pub.get('venue', '')}\nType: {pub.get('type', '')}\nFocus: {pub.get('focus', '')}"
        
        chunks = await embed_and_store(
            text=pub_text,
            source=f"portfolio:publication:{title[:30]}",
            content_type="publication",
            tags=["portfolio", "publication", "research"],
        )
        total_chunks += chunks

    logger.info("portfolio.ingest.complete", total_chunks=total_chunks)
    return total_chunks
