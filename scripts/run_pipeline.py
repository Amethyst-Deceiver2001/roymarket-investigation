#!/usr/bin/env python3
"""Single entry point for the whole РОЙ.МАРКЕТ pipeline — every local stage
run in the correct order, every network stage printed as an exact command
for the user to run themselves.

This does NOT replace CLAUDE.md's crawling-jobs policy, it enforces it
structurally: this script contains no code path that makes a live network
call. It runs the safe/local stages (already-collected-data mining,
registry assembly, verification, graph-building) directly, then prints a
categorized punch list of every network-scale screener with the exact
command to run it, grouped the same way as notes/full_pipeline_catalogue.md.

Usage:
    python3 scripts/run_pipeline.py                 # run all local stages, then print network punch list
    python3 scripts/run_pipeline.py --local-only     # run local stages, skip printing the punch list
    python3 scripts/run_pipeline.py --skip-slow      # skip mine_zakupki.py (can be slow on a large corpus,
                                                      #   see the housekeeping-bundle guidance in CLAUDE.md)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

LOCAL_STAGES = [
    ("inventory_sources.py", []),
    ("scan_sources.py", ["--out", "data/sources/MANIFEST.md"]),
    ("mine_leads.py", []),
    ("mine_zakupki.py", []),  # skippable via --skip-slow, see notes/rebuild history 2026-08-29
    ("extract_registry.py", []),
    ("build_relationship_graph.py", []),
    ("check_registry.py", []),
    ("reverse_source_index.py", []),
    ("graph_quality_report.py", ["--out", "data/registry/relationship_graph_quality.md"]),
    ("build_graph_explorer.py", []),
    ("coverage_report.py", []),
]

# (category, [(script, description, example command)])
NETWORK_STAGES = [
    ("Collection", [
        ("tg_scan.py", "Telegram channel scrape (config/channels.txt)", "python3 scripts/tg_scan.py"),
        ("tg_scan_users.py", "Channel/chat membership roster", "python3 scripts/tg_scan_users.py --only <handle>"),
        ("vk_fetch.py", "VK wall/newsfeed pull", "python3 scripts/vk_fetch.py --help"),
    ]),
    ("Registry identifiers & founding documents", [
        ("egrul_batch_pull.py", "egrul.nalog.ru open lookup, full roster", "python3 scripts/egrul_batch_pull.py"),
        ("egrul_vypiska_pull.py", "Full signed ЕГРЮЛ/ЕГРИП выписка PDFs", "python3 scripts/egrul_vypiska_pull.py --help"),
        ("crosscheck_egrul.py", "Automated fresh-EGRUL cross-check", "python3 scripts/crosscheck_egrul.py"),
        ("screen_egrip_ip.py", "ЕГРИП lookup on personal ИНН, full roster", "python3 scripts/screen_egrip_ip.py"),
        ("checko_pull.py", "checko.ru aggregator pull", "python3 scripts/checko_pull.py --help"),
    ]),
    ("Financials", [
        ("bfo_pull.py", "bo.nalog.gov.ru signed БФО filings", "python3 scripts/bfo_pull.py"),
    ]),
    ("Procurement (44-ФЗ / 223-ФЗ)", [
        ("zakupki_batch_pull.py scan", "Contract search, full roster", "python3 scripts/zakupki_batch_pull.py scan"),
        ("zakupki_batch_pull.py fetch-documents", "Attachment pull for known hits", "python3 scripts/zakupki_batch_pull.py fetch-documents --all-hits"),
        ("screen_rnp.py", "РНП unreliable-supplier registry", "python3 scripts/screen_rnp.py"),
    ]),
    ("Sanctions, PEP & watchlists", [
        ("screen_opensanctions.py", "OpenSanctions batch match", "python3 scripts/screen_opensanctions.py"),
        ("screen_gur.py", "GUR war-sanctions (entities + UAV companies)", "python3 scripts/screen_gur.py"),
        ("screen_gur_components.py", "GUR components teardown catalogue", "python3 scripts/screen_gur_components.py"),
        ("screen_aleph.py", "OCCRP Aleph entity search", "python3 scripts/screen_aleph.py"),
        ("screen_disqualified.py", "ФНС disqualified-director registry", "python3 scripts/screen_disqualified.py"),
        ("screen_subsidiary.py", "ФНС subsidiary-liability cross-check", "python3 scripts/screen_subsidiary.py"),
        ("screen_upr_uchr.py", "ФНС director/founder cross-reference", "python3 scripts/screen_upr_uchr.py"),
        ("screen_rom.py", "ФНС Реестр обеспечительных мер", "python3 scripts/screen_rom.py"),
        ("screen_pledge_registry.py", "Federal Notary Chamber pledge registry", "python3 scripts/screen_pledge_registry.py"),
        ("screen_fssp_opendata.py", "ФССП open-data debt CSV", "python3 scripts/screen_fssp_opendata.py"),
    ]),
    ("Sector licenses & regulatory registries", [
        ("fstec_pull.py", "ФСТЭК reg1/reg2 licence registries", "python3 scripts/fstec_pull.py"),
        ("screen_rosgvardia_licenses.py", "Rosgvardia's 5 license registries", "python3 scripts/screen_rosgvardia_licenses.py"),
        ("screen_mchs_fire_licenses.py", "МЧС fire-safety licenses", "python3 scripts/screen_mchs_fire_licenses.py"),
        ("screen_favt_aviation_operators.py", "favt.gov.ru aviation-works operators", "python3 scripts/screen_favt_aviation_operators.py"),
        ("screen_roscosmos_licenses.py", "Roscosmos space-activity licenses", "python3 scripts/screen_roscosmos_licenses.py"),
        ("screen_rkn_comms_license.py", "RKN communications-license registry", "python3 scripts/screen_rkn_comms_license.py"),
        ("screen_rkn_frequency_registry.py", "RKN frequency-assignment registry", "python3 scripts/screen_rkn_frequency_registry.py"),
        ("pub_fsa_pull.py", "ФГИС Росаккредитация", "python3 scripts/pub_fsa_pull.py"),
        ("reestr_digital_pull.py", "Accredited-IT-company registry", "python3 scripts/reestr_digital_pull.py"),
        ("screen_fas_br.py", "ФАС База решений и правовых актов", "python3 scripts/screen_fas_br.py"),
        ("screen_proverki.py", "ФГИС Единый реестр проверок", "python3 scripts/screen_proverki.py"),
        ("screen_rmsp.py", "Единый реестр СМСП", "python3 scripts/screen_rmsp.py"),
        ("screen_ekg_rating.py", "экг-рейтинг.рф ESG index (added 2026-09-08)", "python3 scripts/screen_ekg_rating.py"),
    ]),
    ("IP (patents & trademarks)", [
        ("rospatent_searchplatform_search.py", "Live patent search API, full roster", "python3 scripts/rospatent_searchplatform_search.py"),
        ("rospatent_tm_ws_search.py", "Live trademark search API, full roster", "python3 scripts/rospatent_tm_ws_search.py"),
        ("rospatent_archive_patents.py", "Archive full patent documents", "python3 scripts/rospatent_archive_patents.py"),
    ]),
    ("State-industry programs & directories", [
        ("screen_rk2035_bas_registry.py", "rk.2035.university БАС directory", "python3 scripts/screen_rk2035_bas_registry.py"),
        ("gisp_goods_pull.js", "gisp.gov.ru product catalog — BROWSER CONSOLE SNIPPET, not python3", "paste into DevTools console per the script's own header"),
    ]),
    ("Property & geography", [
        ("screen_nspd_addresses.py", "Rosreestr НСПД address cross-check", "python3 scripts/screen_nspd_addresses.py"),
    ]),
    ("Marketplace overlap", [
        ("screen_wb.py", "Wildberries seller-record cross-check", "python3 scripts/screen_wb.py"),
    ]),
]


def run(script: str, args: list[str]) -> bool:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=REPO)
    return result.returncode == 0


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)  # keep our own prints interleaved
    # correctly with subprocess output when stdout isn't a tty (e.g. piped/logged)
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-only", action="store_true", help="run local stages only, skip the network punch list")
    ap.add_argument("--skip-slow", action="store_true", help="skip mine_zakupki.py (can be slow over a large corpus)")
    args = ap.parse_args()

    print("=== Stage 1-11: local pipeline (no network calls) ===")
    for script, script_args in LOCAL_STAGES:
        if args.skip_slow and script == "mine_zakupki.py":
            print(f"\n(skipping {script} — --skip-slow)")
            continue
        ok = run(script, script_args)
        if not ok:
            print(f"\n!! {script} exited non-zero — stopping before the next stage.")
            sys.exit(1)

    print("\n=== Local pipeline complete. ===")

    if args.local_only:
        return

    print("\n=== Network stages (per CLAUDE.md's crawling-jobs policy, run these yourself) ===")
    print("Each command below hits a live third-party service across the full registry.")
    print("Run them in your own terminal, not backgrounded. A single --slug/--inn spot-check")
    print("on any of these is fine to run inline for reconnaissance.\n")
    for category, entries in NETWORK_STAGES:
        print(f"## {category}")
        for script, desc, cmd in entries:
            print(f"  {cmd}")
            print(f"      ({desc})")
        print()

    print("After any of the above adds new sources/fields: re-run this script with --local-only")
    print("to re-assemble the registry, or at minimum:")
    print("  python3 scripts/extract_registry.py && python3 scripts/check_registry.py")


if __name__ == "__main__":
    main()
