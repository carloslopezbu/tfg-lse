import polars as pl
import requests
import os

csv_in: str = "data-mining/clean/sts_videos.csv"
csv_out: str = "data-mining/clean/sts_videos_labeled.csv"
videos_path: str = "data-mining/videos/"

df = pl.read_csv(csv_in)

os.makedirs(videos_path, exist_ok=True)


class video_labeler:
    def __init__(self) -> None:
        self.id = 0

    def get_id(self):
        rep = str(self.id)
        n = 5 - len(rep)
        self.id += 1
        return n * "0" + rep + ".mp4"


vl = video_labeler()

# Aquí guardamos los metadatos
records = []

for row in df.iter_rows(named=True):
    video_url = row["video"]
    r = requests.get(video_url, stream=True)
    r.raise_for_status()

    video_name = vl.get_id()
    video_out = os.path.join(videos_path, video_name)

    with open(video_out, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Guardamos los metadatos
    records.append(
        {
            "path": video_out,
            "text": row.get("text", None),
            "type": row.get("type", None),
            "categorie": row.get("categorie", None),
        }
    )

# Convertimos a polars DataFrame y lo guardamos como CSV
df_out = pl.DataFrame(records)
df_out.write_csv(csv_out)

print(f"CSV generado en: {csv_out}")
