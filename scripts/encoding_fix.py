from pathlib import Path

p = Path("frontend/src/main.tsx")
s = p.read_bytes().decode("cp1252")
s = (
    s.replace("?1,00,000", "\u20b91,00,000")
    .replace("?0 / 0%", "\u20b90 / 0%")
    .replace("Published ?${v}", "Published \u20b9${v}")
    .replace(">?{v}<", ">\u20b9{v}<")
)
p.write_text(s, encoding="utf-8")
