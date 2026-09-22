#!/usr/bin/env python3
"""Run VTON pipeline modules separately and write artifacts to ``test_output/``.

Usage::

    cd backend
    python test_modules.py                 # all modules (no Flux GPU call)
    python test_modules.py combinations    # CSV lookup only
    python test_modules.py prompts         # prompt file resolution
    python test_modules.py preprocess      # garment face crop
    python test_modules.py classify        # SigLIP on person + garment
    python test_modules.py mask            # mask region + optional PNG
    python test_modules.py dry             # crop → classify → CSV → prompt

Optional paths (after the module name)::

    python test_modules.py preprocess ..\\images\\f-dress-red.jpg
    python test_modules.py classify ..\\images\\m-suit-navy.jpg ..\\images\\m-shirt-blue.jpg
    python test_modules.py dry ..\\images\\m-suit-navy.jpg ..\\images\\f-dress-red.jpg
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "test_output"
IMAGES = ROOT.parent / "test_images"

sys.path.insert(0, str(ROOT))


def _read(path: Path) -> bytes:
    return path.read_bytes()


def _write_json(name: str, data) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")
    return path


def _default_person() -> Path:
    for name in (
        "images (1).jfif",
        "images (2).jfif",
        "images.jfif",
        "1.png",
        "2.png",
        "3.png",
    ):
        p = IMAGES / name
        if p.is_file():
            return p
    # Any image in the folder
    for p in sorted(IMAGES.iterdir()):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".jfif", ".webp"):
            return p
    raise SystemExit(f"No default person image under {IMAGES}")


def _default_garment() -> Path:
    for name in (
        "6DSHT649-KHK_4 .png",  # note: space before .png on disk
        "6DSHT649-KHK_4.png",
        "6.png",
        "4.png",
        "5.png",
        "7.png",
        "8.png",
        "9.png",
    ):
        p = IMAGES / name
        if p.is_file():
            return p
    for p in sorted(IMAGES.iterdir()):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".jfif", ".webp"):
            return p
    raise SystemExit(f"No default garment image under {IMAGES}")


def _garment_list(extra: list[str]) -> list[Path]:
    if extra:
        return [Path(p) for p in extra]
    exts = ("*.jpg", "*.jpeg", "*.png", "*.jfif", "*.webp")
    files: list[Path] = []
    for pat in exts:
        files.extend(IMAGES.glob(pat))
    return sorted(files)


# ── modules ──────────────────────────────────────────────────────────────


def test_combinations(_: list[str]) -> None:
    import combinations

    rows = combinations.all_combos()
    sample = {
        "shirt_pant+shirt": combinations.lookup_vton_type("shirt_pant", "shirt"),
        "kurta_shalwar+shirt": combinations.lookup_vton_type("kurta_shalwar", "shirt"),
        "shirt_pant+pant": combinations.lookup_vton_type("shirt_pant", "pant"),
        "upper kurta_shalwar+coat supported": combinations.is_supported(
            "upper_body", "kurta_shalwar", "coat"
        ),
    }
    payload = {
        "total_rows": len(rows),
        "sample_lookups": sample,
        "rows": [
            {"vton_type": a, "person_outfit": b, "garment_type": c}
            for a, b, c in rows
        ],
    }
    print(f"[combinations] {len(rows)} CSV rows")
    for k, v in sample.items():
        print(f"  {k}: {v}")
    _write_json("01_combinations.json", payload)


def test_prompts(_: list[str]) -> None:
    import prompts

    coverage = prompts.list_coverage()
    ok = sum(1 for r in coverage if r["ok"])
    print(f"[prompts] {ok}/{len(coverage)} CSV rows have a prompt file")
    for r in coverage:
        status = "OK" if r["ok"] else "MISSING"
        label = r.get("prompt") or r.get("error", "")
        print(
            f"  [{status}] {r['vton_type']}/{r['person_outfit']}->{r['garment_type']}"
            f"  {label}"
        )
    _write_json("02_prompts.json", coverage)
    missing = [r for r in coverage if not r["ok"]]
    if missing:
        print(f"[prompts] WARNING: {len(missing)} combos lack a prompt file")
        for r in missing:
            print(f"  - {r['vton_type']}/{r['person_outfit']}->{r['garment_type']}")


def test_preprocess(args: list[str]) -> None:
    import garment_preprocess

    paths = _garment_list(args)
    if not paths:
        raise SystemExit("No garment images to preprocess")

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for img_path in paths:
        raw = _read(img_path)
        cropped_bytes, meta = garment_preprocess.preprocess_garment(raw)
        row = {"file": img_path.name, **meta}
        results.append(row)
        if meta.get("cropped"):
            out_png = OUT / f"04_crop_{img_path.stem}.png"
            out_png.write_bytes(cropped_bytes)
            print(
                f"[preprocess] cropped {img_path.name} → {out_png.name} "
                f"(y={meta.get('crop_y')})"
            )
        else:
            print(f"[preprocess] {img_path.name}: {meta.get('reason', 'unchanged')}")

    _write_json("04_garment_preprocess.json", results)
    cropped_n = sum(1 for r in results if r.get("cropped"))
    print(f"[preprocess] {cropped_n}/{len(results)} images cropped")


def test_classify(args: list[str]) -> None:
    import classify
    import garment_preprocess

    if len(args) >= 2:
        person_path, garment_path = Path(args[0]), Path(args[1])
    elif len(args) == 1:
        person_path, garment_path = _default_person(), Path(args[0])
    else:
        person_path, garment_path = _default_person(), _default_garment()

    print(f"[classify] person={person_path.name}  garment={garment_path.name}")

    person_bytes = _read(person_path)
    garment_bytes, crop_meta = garment_preprocess.preprocess_garment(
        _read(garment_path)
    )
    print(f"  garment crop: {crop_meta}")

    person_scores = classify.classify_person(person_bytes)
    garment_scores = classify.classify_garment(garment_bytes)

    def _show(title: str, scores: list) -> None:
        print(f"  {title}:")
        for s in scores[:5]:
            conf = ""
            if "confident" in s:
                conf = f"  confident={s['confident']} margin={s.get('margin')}"
            print(
                f"    {s['label']:16s}  score={s['score']:.4f}  "
                f"peak={s['peak']:.4f}{conf}"
            )

    _show("person_outfit", person_scores)
    _show("garment_type", garment_scores)

    payload = {
        "person_image": person_path.name,
        "garment_image": garment_path.name,
        "garment_crop": crop_meta,
        "person_classify": person_scores,
        "garment_classify": garment_scores,
        "top": {
            "person_outfit": person_scores[0]["label"] if person_scores else None,
            "garment_type": garment_scores[0]["label"] if garment_scores else None,
        },
    }
    _write_json("05_classify.json", payload)


def test_mask(args: list[str]) -> None:
    import mask as mask_mod

    person_path = Path(args[0]) if args else _default_person()
    person_bytes = _read(person_path)

    # Demo regions for the person photo.
    regions = ["upper", "upper_long", "lower", "full"]
    region_meta = {}
    OUT.mkdir(parents=True, exist_ok=True)

    for region in regions:
        try:
            out_bytes = mask_mod.build_agnostic(person_bytes, region)
            out_path = OUT / f"03_mask_{region}.png"
            out_path.write_bytes(out_bytes)
            region_meta[region] = {"ok": True, "file": out_path.name}
            print(f"[mask] {region} → {out_path.name}")
        except Exception as e:
            region_meta[region] = {"ok": False, "error": str(e)}
            print(f"[mask] {region} FAILED: {e}")

    # Also show CSV-driven region mapping samples.
    samples = [
        ("upper_body", "shirt_pant", "shirt"),
        ("upper_body", "kurta_shalwar", "shirt"),
        ("upper_body", "shirt_pant", "jacket"),
        ("lower_body", "shirt_pant", "pant"),
        ("full_body", "shirt_pant", "kurta_shalwar"),
    ]
    mapping = []
    for vton, person, garment in samples:
        region = mask_mod.region_for_vton_type(vton, person, garment)
        mapping.append({
            "vton_type": vton,
            "person_outfit": person,
            "garment_type": garment,
            "mask_region": region,
        })
        print(f"  map {vton}/{person}→{garment}: {region}")

    _write_json(
        "03_mask_regions.json",
        {"person_image": person_path.name, "regions": region_meta, "mapping": mapping},
    )


def test_dry(args: list[str]) -> None:
    import garment_preprocess
    import mask as mask_mod
    import classify
    import combinations
    import prompts as prompts_mod

    if len(args) >= 2:
        person_path, garment_path = Path(args[0]), Path(args[1])
    elif len(args) == 1:
        person_path, garment_path = _default_person(), Path(args[0])
    else:
        person_path, garment_path = _default_person(), _default_garment()

    print(f"[dry] person={person_path.name}  garment={garment_path.name}")
    OUT.mkdir(parents=True, exist_ok=True)

    person_bytes = _read(person_path)
    garment_raw = _read(garment_path)
    cropped, crop_meta = garment_preprocess.preprocess_garment(garment_raw)
    print(f"  garment_crop  = {crop_meta}")
    if crop_meta.get("cropped"):
        (OUT / "06_cropped_garment.png").write_bytes(cropped)
        print("  saved 06_cropped_garment.png")

    person_scores = classify.classify_person(person_bytes)
    garment_scores = classify.classify_garment(cropped)
    person_outfit = person_scores[0]["label"] if person_scores else None
    garment_type = garment_scores[0]["label"] if garment_scores else None
    print(f"  person_outfit = {person_outfit}")
    print(f"  garment_type  = {garment_type}")
    if person_scores:
        print(f"    person top scores: "
              + ", ".join(f"{s['label']}={s['score']:.3f}" for s in person_scores[:3]))
    if garment_scores:
        print(f"    garment top scores: "
              + ", ".join(f"{s['label']}={s['score']:.3f}" for s in garment_scores[:3]))

    vton_type = combinations.lookup_vton_type(person_outfit, garment_type) if (
        person_outfit and garment_type
    ) else None
    print(f"  vton_type     = {vton_type}")

    prompt_label = None
    prompt_text = None
    mask_region = None
    error = None

    if not vton_type:
        error = (
            f"unsupported combo: person_outfit={person_outfit}, "
            f"garment_type={garment_type}"
        )
        print(f"  ERROR: {error}")
    else:
        try:
            prompt_text, prompt_label = prompts_mod.get_prompt(
                vton_type, person_outfit, garment_type
            )
            print(f"  prompt_label  = {prompt_label}")
            mask_region = mask_mod.region_for_vton_type(
                vton_type, person_outfit, garment_type
            )
            print(f"  mask_region   = {mask_region}")
            if mask_region:
                try:
                    masked = mask_mod.build_agnostic(person_bytes, mask_region)
                    (OUT / "06_masked_person.png").write_bytes(masked)
                    print(f"  saved 06_masked_person.png (region={mask_region})")
                except Exception as e:
                    print(f"  mask PNG skipped: {e}")
            print("  prompt_preview:")
            preview = prompt_text[:220] + ("..." if len(prompt_text) > 220 else "")
            for line in preview.splitlines()[:8]:
                print(f"    {line}")
            (OUT / "06_prompt.txt").write_text(prompt_text, encoding="utf-8")
            print("  wrote test_output/06_prompt.txt")
        except FileNotFoundError as e:
            error = str(e)
            print(f"  ERROR: {error}")

    summary = {
        "person_image": person_path.name,
        "garment_image": garment_path.name,
        "person_outfit": person_outfit,
        "garment_type": garment_type,
        "vton_type": vton_type,
        "prompt_label": prompt_label,
        "mask_region": mask_region,
        "garment_crop": crop_meta,
        "person_classify": person_scores,
        "garment_classify": garment_scores,
        "prompt_preview": (prompt_text[:220] + "...") if prompt_text else None,
        "prompt_chars": len(prompt_text) if prompt_text else 0,
        "error": error,
        "ok": error is None,
    }
    _write_json("06_pipeline_dry.json", summary)
    if error:
        raise SystemExit(1)


MODULES = {
    "combinations": test_combinations,
    "prompts": test_prompts,
    "preprocess": test_preprocess,
    "classify": test_classify,
    "mask": test_mask,
    "dry": test_dry,
}

DEFAULT_ORDER = [
    "combinations",
    "prompts",
    "preprocess",
    "mask",
    "classify",
    "dry",
]


def main(argv: list[str]) -> None:
    if argv and argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("Modules:", ", ".join(MODULES))
        return

    if not argv:
        order = DEFAULT_ORDER
        rest: list[str] = []
    else:
        name = argv[0]
        if name not in MODULES:
            raise SystemExit(
                f"Unknown module {name!r}. Choose from: {', '.join(MODULES)}"
            )
        order = [name]
        rest = argv[1:]

    for mod in order:
        print(f"\n=== {mod} ===")
        MODULES[mod](rest)


if __name__ == "__main__":
    main(sys.argv[1:])
