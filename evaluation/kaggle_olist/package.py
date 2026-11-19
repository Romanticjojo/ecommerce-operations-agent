"""Build the standalone acceptance archive from a reviewed file allowlist."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

pack = Path(__file__).resolve().parent
root = pack.parents[1]
files = [
    root / "LICENSE",
    root / "requirements.txt",
    root / "requirements.lock",
    root / "evaluation" / "questions.json",
    *sorted((root / "commerce").glob("*.py")),
    *sorted((root / "tests").glob("test_*.py")),
    pack / "README.md",
    pack / "requirements.txt",
    pack / "media" / "K03-revenue.mp4",
    pack / "media" / "K03-results.json",
    *sorted(pack.glob("*.py")),
    *(
        pack / "verified" / name
        for name in ("REPORT.md", "results.json", "manifest.json")
    ),
]
with ZipFile(pack / "olist-kaggle-acceptance.zip", "w") as bundle:
    for name, source in [
        ("README.md", pack / "README.md"),
        *((p.relative_to(root).as_posix(), p) for p in files),
    ]:
        info = ZipInfo("olist-kaggle-acceptance/" + name)
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        content = source.read_bytes()
        if name == "README.md":
            content = content.replace(
                b"](verified/", b"](evaluation/kaggle_olist/verified/"
            ).replace(b"](media/", b"](evaluation/kaggle_olist/media/")
        bundle.writestr(info, content)
