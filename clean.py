import marimo

__generated_with = "0.16.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Limpieza de los datos""")
    return


@app.cell
def _():
    import os # utilidades del sistema operativo
    import json # utilidades de json
    import polars as pl # dataframes optimizados
    from unidecode import unidecode # quitar tildes
    import urllib.parse
    return json, os, pl, urllib


@app.cell
def _():
    path_raw_txt: str = 'data-mining/raw/txt/' # path a los datos sin limpiar
    path_raw_json: str = 'data-mining/raw/json/' # path a los datos en json
    path_clean: str = 'data-mining/clean/'
    return path_clean, path_raw_json, path_raw_txt


@app.cell
def _(json, os, path_raw_json: str, path_raw_txt: str):
    for file in os.listdir(path_raw_txt): # iteramos en la caperta con los ficheros categoria.txt (bad json)
        rows = []
        categorie: str = file.split('.')[0]
        with open(path_raw_txt + file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line) # cargamos diccionarios
                data['categorie'] = categorie
                if type(data['video']) == list: # Estaba como lista ahora sera cadena
                    assert len(data['video']) == 1
                    data['video'] = data['video'][0]
                rows.append(data) # añadimos 

            with open(path_raw_json + file.split('.')[0] + '.json', 'w') as json_file:
                json.dump(rows, json_file, indent=3) # guardamos json limpios
    return


@app.cell
def _(os, path_raw_json: str, pl, urllib):
    dfs = [pl.read_json(os.path.join(path_raw_json, p)) for p in os.listdir(path_raw_json)] # leer todos los json a dataframe
    df = pl.concat(dfs, how="vertical") # concatenar

    def extract_word(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(parsed.query).get("q", [""])[0]
        return urllib.parse.unquote(q).replace("+", " ")

    # Aplicar con map_elements
    df = df.with_columns(
        df["href"].map_elements(extract_word, return_dtype=pl.Utf8).alias("text")
    ) # había problemas con el nombre de las palabras
    return (df,)


@app.cell
def _(df, path_clean: str, pl):
    dictionary = pl.DataFrame(
        df['text']
        .unique()
        .sort()
    )


    dictionary.write_csv(path_clean + 'dictionary.csv')
    return


@app.cell
def _(df):
    videos = df.filter(df['video'] != 'no-video')['text', 'type', 'categorie', 'video'] #
    videos.filter(videos['type'] == 'unknow') # ver si hay videos sin tipo semántico
    return (videos,)


@app.cell
def _(path_clean: str, pl, videos):
    filtered_videos: pl.DataFrame = videos.with_columns(
        videos['type'].replace({"unknow": "Nombre"}).alias("type") # quitar unknow (todos deberían ser nombre)
    )

    filtered_videos = filtered_videos.with_columns(
        filtered_videos['type']
        .map_elements(str.lower)   # todo en minúsculas
        .alias("type")             # reemplazar la columna "type"
    )

    filtered_videos.write_csv(path_clean + 'sts_videos.csv')
    return


if __name__ == "__main__":
    app.run()
