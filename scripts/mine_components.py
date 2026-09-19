#!/usr/bin/env python3
"""Mine stored Telegram post text for drone components/tools/software named by manufacturers.

Local processing over data/roymarket.db, no network. Output is a triage list: a hit is a
lead (which channel names which part), not a verified fact. Extend LEXICON as new terms turn up.

  python3 scripts/mine_components.py --out data/registry/_components_mined.md
  python3 scripts/mine_components.py --channel Archangel_Forum --category fc_esc
"""
import argparse, collections, json, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "roymarket.db"

# category -> {canonical name: regex}. Case-insensitive; Latin and Cyrillic spellings.
LEXICON = {
    "fc_esc": {
        "SpeedyBee": r"speedy\s?bee|спиди\s?би",
        "BeastFPV": r"beast\s?fpv|бист\s?fpv",
        "Betaflight": r"betaflight|бета\s?флайт",
        "INAV": r"\binav\b|инав",
        "ArduPilot": r"ardu\s?pilot|ардупилот",
        "PX4": r"\bpx4\b",
        "Pixhawk/Cube": r"pixhawk|пиксхок|cube\s?orange|cube\s?black",
        "Matek": r"\bmatek\b|матек",
        "iFlight": r"\biflight\b|ифлайт",
        "Holybro": r"holybro|холибро",
        "STM32": r"stm32",
        "Полётный контроллер (generic term)": r"полетн\w+\s+контроллер|полётн\w+\s+контроллер",
    },
    "camera_optics": {
        "Caddx": r"caddx|каддкс|кадэкс",
        "RunCam": r"runcam|ранкам",
        "Foxeer": r"foxeer|фоксир",
        "DJI": r"\bdji\b|дджи|ди-?джей-?ай|mavic|мавик|matrice|матрис|autel|аутел",
        "Тепловизор": r"тепловизор|тепляк|infiray|инфирей|guide\s?sensmart",
        "Hikvision/Dahua": r"hikvision|dahua",
    },
    "video_radio": {
        "GEPRC": r"geprc|геп\s?рс",
        "TBS/Crossfire": r"crossfire|кроссфайр|\btbs\b|tracer",
        "ExpressLRS": r"expresslrs|\belrs\b|эльрс|erls",
        "RadioMaster": r"radiomaster|радиомастер",
        "Гермес": r"гермес|hermes",
        "Кузнечик": r"кузнечик",
        "Walksnail/HDZero": r"walksnail|hdzero|аналог\w*\s+видео",
        "Happymodel": r"happymodel|хеппимодел",
        "Mesh/Doodle": r"doodle\s?labs|mesh\s?rider|рупор|silvus",
    },
    "propulsion_power": {
        "BrotherHobby": r"brother\s?hobby|бразер\s?хобби|брат\w*\s+хобби",
        "T-Motor": r"t-?motor|т-?мотор",
        "HQProp": r"hq\s?prop|hqprop",
        "Gemfan": r"gemfan|джемфан",
        "Tattu/GNB": r"tattu|\bgnb\b|таттu",
        "LiHV": r"lihv",
    },
    "nav_compute": {
        "Starlink": r"starlink|старлинк",
        "GNSS/GPS": r"\bgnss\b|\bglonass\b|глонасс|\bgps\b|kometa|комета|краст",
        "Jetson/RPi": r"jetson|raspberry|распберри|orange\s?pi|rockchip|rk3588",
        "ИИ/нейросеть": r"нейросет|нейронн|искусственн\w+\s+интеллект|\bии\b|yolo|opencv",
        "Рой/swarm": r"\bрой\b|роев\w+",
    },
    "software_tools": {
        "Bambulab": r"bambu\s?lab|бамбу\s?лаб|x1\s?carbon",
        "CAD (SolidWorks/Fusion/Компас)": r"solid\s?works|fusion\s?360|компас-?3d|kompas|autocad|freecad",
        "Mission Planner/QGC": r"mission\s?planner|qgroundcontrol|\bqgc\b",
        "Configurator": r"конфигуратор|configurator",
        "Telegram-боты": r"телеграм-?бот|\bbot\b",
    },
    "munition_payload": {
        "боевая часть/БЧ": r"боев\w+\s+част\w+|\bбч\b",
        "ВОГ/кумулятив": r"\bвог\b|кумулятив|осколочн|\bрпг\b|тротил|гексоген|c-?4",
        "сброс/боеприпас": r"сброс\w*|боеприпас|боекомплект",
        "полезная нагрузка": r"полезн\w+\s+нагрузк|загружат\w+\s+\d+",
    },
}

COMPILED = {
    cat: {name: re.compile(rx, re.I) for name, rx in terms.items()} for cat, terms in LEXICON.items()
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", help="channel username to restrict to")
    ap.add_argument("--category", help="one LEXICON category")
    ap.add_argument("--min-posts", type=int, default=3, help="min posts for a channel/term pair")
    ap.add_argument("--out", help="write a markdown report here")
    ap.add_argument("--json-out", help="write raw counts JSON here")
    a = ap.parse_args()

    con = sqlite3.connect(DB)
    chan = {r[0]: r[1] or str(r[0]) for r in con.execute("select id, username from tg_channels")}
    sql = "select channel_id, msg_id, date, media_type, text from tg_posts where text is not null and text != ''"
    args: list = []
    if a.channel:
        ids = [k for k, v in chan.items() if v.lower() == a.channel.lower()]
        if not ids:
            print("unknown channel", a.channel, file=sys.stderr)
            return 2
        sql += " and channel_id = ?"
        args.append(ids[0])

    cats = {a.category: COMPILED[a.category]} if a.category else COMPILED
    counts = collections.defaultdict(lambda: collections.defaultdict(int))  # (cat,name) -> channel -> n
    video = collections.defaultdict(lambda: collections.defaultdict(int))
    examples: dict = {}
    total = 0
    for ch, mid, date, mtype, text in con.execute(sql, args):
        total += 1
        for cat, terms in cats.items():
            for name, rx in terms.items():
                if rx.search(text):
                    key = (cat, name)
                    counts[key][chan.get(ch, str(ch))] += 1
                    if mtype == "video":
                        video[key][chan.get(ch, str(ch))] += 1
                    examples.setdefault((key, chan.get(ch, str(ch))), (mid, date[:10], text[:160].replace("\n", " ")))

    lines = [f"# Component/tool mentions in stored posts\n\nScanned {total} posts. Triage list, not facts.\n"]
    raw = {}
    for cat in cats:
        lines.append(f"\n## {cat}\n")
        for name in cats[cat]:
            per = counts.get((cat, name), {})
            n = sum(per.values())
            if not n:
                continue
            raw[f"{cat}/{name}"] = dict(per)
            lines.append(f"### {name} - {n} posts, {len(per)} channels")
            for chn, c in sorted(per.items(), key=lambda kv: -kv[1]):
                if c < a.min_posts and len(per) > 8:
                    continue
                ex = examples[((cat, name), chn)]
                v = video[(cat, name)].get(chn, 0)
                lines.append(f"- @{chn}: {c} posts ({v} with video); e.g. #{ex[0]} {ex[1]}: {ex[2]}")
            lines.append("")
    out = "\n".join(lines)
    if a.out:
        Path(a.out).write_text(out)
        print("wrote", a.out)
    else:
        print(out)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
