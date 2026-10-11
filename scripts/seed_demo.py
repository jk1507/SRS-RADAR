"""
Seed the demo (PRD Section 14 DevEx):
1. logs in as the seeded demo user
2. creates 3 projects from the sample SRS fixtures
3. uploads each fixture, runs the full analysis pipeline
4. prints verified results (scores, issue counts, key detections)

Usage:  python scripts/seed_demo.py [base_url]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = f"{BASE}/api/v1"
ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "eval" / "fixtures"

PROJECTS = [
    ("smart-hospital-srs-v1.3.docx", "Smart Hospital Core SRS", "Medical / Healthcare",
     "Electronic Health Records & Medical IoT Telemetry Intake Specification."),
    ("drone-navigation-srs-v2.1.docx", "Autonomous Drone Navigation SRS", "Aerospace / Robotics",
     "Real-time obstacle avoidance and swarm synchronization specification."),
    ("payment-gateway-srs-v0.9.docx", "FinTech Gateway API Spec", "Financial Services",
     "ISO 20022 compliant payment processing engine specification."),
]


def main() -> None:
    with httpx.Client(base_url=API, timeout=120.0) as c:
        # ---- auth -------------------------------------------------------
        r = c.post("/auth/login", json={
            "email": "jack@requirement-radar.dev", "password": "radar-demo-2026"})
        r.raise_for_status()
        token = r.json()["access_token"]
        hdr = {"Authorization": f"Bearer {token}"}
        print(f"[auth] logged in as {r.json()['user']['name']} "
              f"({r.json()['user']['role']})")

        for filename, name, domain, description in PROJECTS:
            path = FIXTURES / filename
            if not path.exists():
                print(f"[skip] fixture missing: {path}")
                continue

            # remove any previous run of the same project (idempotent seed)
            existing = c.get("/projects", headers=hdr).json()
            prior = next((p for p in existing if p["name"] == name), None)
            if prior:
                print(f"[project] deleting previous '{name}'")
                c.delete(f"/projects/{prior['id']}", headers=hdr)

            r = c.post("/projects", headers=hdr, json={
                "name": name, "domain": domain, "description": description,
                "version": "v1.0", "lint_mode": "Standard",
                "retention_mode": "standard"})
            r.raise_for_status()
            project = r.json()
            print(f"[project] created {name} ({project['id']})")

            with path.open("rb") as fh:
                r = c.post(f"/projects/{project['id']}/documents", headers=hdr,
                           files={"file": (filename, fh,
                                           "application/vnd.openxmlformats-officedocument."
                                           "wordprocessingml.document")},
                           data={"start_analysis": "true", "mode": "standard_audit"})
            r.raise_for_status()
            body = r.json()
            run_id = body["run"]["id"]
            print(f"[upload] {filename} -> run {run_id}")

            # ---- poll until finished -------------------------------------
            status = "in_progress"
            t0 = time.time()
            while status in ("pending", "in_progress") and time.time() - t0 < 600:
                time.sleep(2)
                s = c.get(f"/analysis/{run_id}/status", headers=hdr).json()
                status = s["status"]
                print(f"   {s['percentage']:5.1f}%  stage={s['stage'][:48]:48} "
                      f"proc={s['processed']}/{s['total']} eta={s['eta_seconds']}s",
                      end="\r")
            print()
            if status != "completed":
                detail = c.get(f"/analysis/{run_id}", headers=hdr).json()
                print(f"[FAIL] run ended as {status}: {detail.get('error')}")
                for log in (detail.get("logs") or [])[-8:]:
                    print("   ", log)
                continue

            summary = c.get(f"/projects/{project['id']}/summary", headers=hdr).json()
            counts = c.get("/issues/counts",
                           params={"project_id": project["id"]}, headers=hdr).json()
            print(f"[done] score={summary['quality_score']} "
                  f"reqs={summary['total_requirements']} "
                  f"issues(open/total)={counts['open']}/{counts['total']} "
                  f"by_sev={counts['open_by_severity']}")

            # ---- highlight key detections --------------------------------
            issues = c.get("/issues", params={"project_id": project["id"]},
                           headers=hdr).json()
            for i in issues[:6]:
                print(f"   - [{i['severity']}] {i['issue_type']}: {i['title']} "
                      f"({i['verification_status']}, conf={i['confidence']})")
            run_info = c.get(f"/analysis/{run_id}", headers=hdr).json()
            print(f"   llm_status={run_info['llm_status']} "
                  f"elapsed={run_info['elapsed_seconds']}s")

    print("\n[seed] complete")


if __name__ == "__main__":
    main()
