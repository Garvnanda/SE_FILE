import zipfile

with zipfile.ZipFile(".runtime/postgres.zip") as z:
    for item in z.infolist():
        if item.filename.startswith(("pgsql/bin/", "pgsql/lib/", "pgsql/share/")):
            z.extract(item, ".runtime")
