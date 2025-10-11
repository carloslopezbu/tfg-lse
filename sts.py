import marimo

__generated_with = "0.16.3"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
    # Extración de datos de la página *_Spread the Sign_*
    """
    ).center()
    return


@app.cell
def _(mo):
    mo.md(
        """
    El objetivo de este cuaderno de este cuaderno es la extración de información de los signos de lengua de señas de la página web _https://spreadthesign.com_.

    La página mencionada presenta una estructura con categoría indexadas en **HTML**, esto hace muy sencillo que podamos extraer información con `web scrapping`.

    Recorreremos las categorías de la página web, almacenando:

    - **text**: La palabra que hace referencia al signo.
    - **grammar-categorie**: La categoría gramatical _(Nombre, Verbo ...)_
    - **categorie**: Categoría temática del signo
    - **video**: Enlace al video del signante

    De manera paralela se construirá un diccionario de palabras _(signos)_ para uso futuro en la extracción de datos de la página web de **CNSE**.
    """
    )
    return


@app.cell
def _():
    import os  # utilidades del sistemo operativo
    import sys  # Para la salida de error
    import json  # para carga y guardado de json
    import requests  # para hacer peticiones http simples
    import urllib.parse  # utilidades de parseo de url´s
    import polars as pl  # dataframes optimizados
    from bs4 import BeautifulSoup  # parseo de html
    from unidecode import unidecode  # para tranformar carácteres
    from trie import Trie  # para almacenamiento de prefijos de manera eficiente

    return BeautifulSoup, Trie, json, os, pl, requests, sys, unidecode, urllib


@app.cell
def _(mo):
    mo.md(r"""## 1. Obtención de las categorías de la página""")
    return


@app.cell
def _():
    sts_url: str = "https://spreadthesign.com"  # root de la página original
    sts_categories: str = (
        f"{sts_url}/es.es/search/by-category/"  # url de la página de las categorías
    )
    return sts_categories, sts_url


@app.cell
def _():
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    }  # Header para hacer peticiones generales
    return (headers,)


@app.cell
def _(headers: dict[str, str], requests, sts_categories: str):
    sts_categories_page = requests.get(
        sts_categories, headers=headers
    )  # hmtl de la página de las categorías
    return (sts_categories_page,)


@app.cell
def _(BeautifulSoup, Trie, sts_categories_page, unidecode):
    sts_categories_soup = BeautifulSoup(
        sts_categories_page.text, "html.parser"
    )  # parseamos html de las categorías

    categories = sts_categories_soup.find(id="categories").find_all(
        "li", recursive=False
    )  # encontramos todas las listas, solo padre

    categories_links = [
        {"href": tag["href"], "gloss": unidecode(tag.get_text()).lower()}
        for cat in categories
        for tag in cat.find_all(
            "a", href=True, recursive=False
        )  # Solo el primero no los hijos
    ]  # Obtenemos todos los enlace en de las listas en formato {"'"href"'": "'"referencia"'", "'"text"'": "'"categoria"'"}

    repeted: Trie = Trie()  # Creamos un trie para categorías no repetidas
    categories_links_filtered = []  # lista con las categorias filtradas

    for cat in categories_links:
        if not repeted.contains(cat["gloss"]):
            categories_links_filtered.append(cat)
            repeted.insert(cat["gloss"])

    categories_links = categories_links_filtered  # Sustituimos la lista filtrada
    categories_links
    return (categories_links,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 2. Obtención de información de las categorías

    Al atravesar las categorías nos encontramos con los signos indexados en el **HTML**, de ahí obtenemos y procesamos texto o nombre del signo, tipo semántico y el video.

    Los datos de cada signo normalmente era del tipo `"\n        palabra\n        \n          tipo-palabra\n"` _(Algunas no)_.

    Este formato se mapea a `{"text": palabra, "grammar-categorie": tipo-palabra}`, si en algún caso no se puede hacer el parseo se pone el texto como esta en el formato sin parsear y se pone el tipo semático `"unknow"`.
    """
    )
    return


@app.function
# "'"\n        palabra\n        \n          tipo-palabra\n"'"  ->  {"'"text"'": palabra, "'"grammar-categorie"'": tipo-palabra}
def format_text_type(text: str):
    if "\n" not in text:
        return {"gloss": text, "grammar-categorie": "next-page"}

    try:
        _, word, _, wtype, _ = text.split("\n")
        word = word.split(" ")[-1]
        wtype = wtype.split(" ")[-1]
    except (RuntimeError, ValueError):
        return {"gloss": text, "grammar-categorie": "unknow"}

    return {"gloss": word, "grammar-categorie": wtype}


@app.cell
def _(mo):
    mo.md(
        r"""
    ### 2.1 Obtención de los enlaces de las temáticas _(signos)_
    Las temáticas se obtienen a través de los enlaces indexados en el **HTML**, algunas páginas tienen enlace de siguiente página, estos enlace tambien se incluyeron en la búsqueda, ya que son puente a nuevas temáticas no registradas.
    """
    )
    return


@app.cell
def _(BeautifulSoup):
    from collections import deque

    def get_theme_links(soup: BeautifulSoup) -> deque:
        search_row = soup.find(id="search-row")
        theme_links = [
            {"href": l["href"], **format_text_type(l.get_text())}
            for l in search_row.find_all("a")
        ]

        only_theme_links = [
            link for link in theme_links if link["grammar-categorie"] != "next-page"
        ]  # todos los enlaces que no son página de siguiente

        next_pages_links = [
            np for np in theme_links if np["grammar-categorie"] == "next-page"
        ]  # lo enlaces que son de páginas siguiente o previa
        theme_links = only_theme_links

        if len(next_pages_links) > 0:
            theme_links += [
                next_pages_links[-1]
            ]  # Si hay página siguiente cogemos la última que sera la página siguiente

        return deque(theme_links)

    return deque, get_theme_links


@app.class_definition
class bcolors:  # Colores !!!
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


@app.cell
def _(mo):
    mo.md(
        r"""
    ## 3. Atravesando la página

    Para la recolección de información de la información que se comentó en las anteriores secciones, se realiza una búsqueda en anchura por categorías, se trata la página como un grafo, en este caso árbol con aristas con retrocesos (enlaces previo y siguiente).

    Para mantener un registro de los `"nodos"` visitados, usamos un árbol de prefijos `"Trie"`, que guarda el registro de los enlaces de las páginas siguiente y previo.

    Al seleccionar los enlaces, donde se incluyen los enlaces previo y siguiente, en algunos casos estos aparencen dos veces, es decir, `[previo, siguiente]` o tambien  `[previo, siguiente, previo, siguiente]`, en cualquiera de los casos siempre cogemos el útlimo de la lista que será siempre el enlace de siguiente, en el caso de que no hubiera se toma como un nodo terminal.
    """
    )
    return


@app.cell
def _(current_cat):
    path_raw_txt: str = "data-mining/raw/txt/"  # path a los datos sin limpiar
    global current_cat  # para tener in registro de la útlima categoría visitada en caso de error
    return (path_raw_txt,)


@app.cell
def _(
    BeautifulSoup,
    Trie,
    categories_links,
    deque,
    get_theme_links,
    headers: dict[str, str],
    json,
    os,
    path_raw_txt: str,
    requests,
    sts_url: str,
    sys,
):
    def get_sts_videos():
        visited_next_pages = Trie()  # trie para evitar revisitar paginas siguiente
        current_cat = 0
        theme_links = deque()
        try:
            for cat_link in categories_links:  # iteramos sobre todas las cateogrias (Parar si va lento, recuperar por categoria)
                # hacemos copia de seguridad por cateroría (⚠️ repetidos por categoría)
                file_name = f"{cat_link['text'].replace(' ', '-')}.txt"
                file_name = os.path.join(path_raw_txt, file_name)
                with open(f"{file_name}.txt", "w", encoding="utf-8") as file:
                    print(
                        f"Guardando copia de seguridad en {bcolors.OKGREEN + file_name + bcolors.ENDC}"
                    )
                    current_cat += (
                        1  # por seguridad rastreamos en que categoria nos quedamos
                    )

                    print(f"Última categoria visitada (índice) {current_cat}")

                    current_url: str = f"{sts_url}{cat_link['href']}"  # url de la página de categoría actual
                    print(
                        f"Accediendo a la categoria {
                            bcolors.BOLD
                            + bcolors.UNDERLINE
                            + cat_link['text']
                            + bcolors.ENDC
                        } desde {bcolors.OKBLUE + sts_url}{cat_link['href']}"
                        + bcolors.ENDC
                    )

                    category_page = requests.get(
                        current_url, headers=headers
                    )  # obtenemos el html de la página de la categoría
                    category_soup = BeautifulSoup(
                        category_page.text, "html.parser"
                    )  # parseamos html de la página

                    theme_links.extend(
                        get_theme_links(category_soup)
                    )  # obtenemos todos los enlaces de la página

                    while theme_links:
                        theme = theme_links.popleft()  # sacamos un enlace de la cola

                        is_theme_page: bool = (
                            theme["grammar-categorie"] != "next-page"
                        )  # saber si es una temática o una página siguiente
                        page_url: str = f"{sts_url if is_theme_page else current_url}{theme['href']}"  # url correcto para la página

                        page = requests.get(
                            page_url, headers=headers
                        )  # obtenemos la página a partir del enlace
                        page_soup = BeautifulSoup(
                            page.text, "html.parser"
                        )  # parseamos hmtl de la página

                        if is_theme_page:
                            print(f"Accediendo a la temática {theme['text']}")

                            video = page_soup.find_all("video")  # buscar videos
                            if not video:
                                print(
                                    f"No hay video para {theme['text']}",
                                    file=sys.stderr,
                                )
                                theme["video"] = (
                                    "no-video"  # si no hay video lo especificamos
                                )

                            else:
                                theme["video"] = [
                                    src["src"] for src in video
                                ]  # guardamos todos los videos (al menos uno)

                            stringified = json.dumps(theme)  # convertimos a cadena
                            file.write(
                                stringified + "\n"
                            )  # guardamos en la copia de seguridad

                        else:
                            if not visited_next_pages.contains(
                                page_url
                            ):  # si no tenemos ese enlace de página siguiente
                                next_theme_links: deque = get_theme_links(
                                    page_soup
                                )  # obtenemos todos los enlaces de la siguiente página
                                print(
                                    f"Añadiendo la siguiente página desde {bcolors.OKBLUE + bcolors.UNDERLINE + page_url + bcolors.ENDC}"
                                )
                                theme_links.extend(
                                    next_theme_links
                                )  # añadimos a la cola
                                visited_next_pages.insert(
                                    page_url
                                )  # guardamos como enlace visitado

        except (RuntimeError, ValueError):
            print("Error", file=sys.stderr)
            return current_cat
        return current_cat

    return (get_sts_videos,)


@app.cell
def _(mo):
    button = mo.ui.button(
        value=False,
        on_click=lambda value: not value,
        label="Ejecutar ⚠️",
        kind="danger",
        tooltip="Al pulsar este botón ejecutaras un proceso extensivo en recursos y tiempo",
    )
    button
    return (button,)


@app.cell
def _(button, get_sts_videos):
    if button.value:
        backup = get_sts_videos()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## 4. Limpieza y transformación de los datos""")
    return


@app.cell
def _():
    path_raw_json: str = "data-mining/raw/json/"  # path a los datos en json
    path_clean: str = "data-mining/clean/"  # path a la salida de los datos limpios
    return path_clean, path_raw_json


@app.cell
def _(mo):
    mo.md(
        r"""Ahora vamos a recorrer los ficheros `.txt` que se guardaron de las copias de seguridad que estan en formato diccionario por linea, lo convertiremos a `json`"""
    )
    return


@app.cell
def _(json, os, path_raw_json: str, path_raw_txt: str):
    for file in os.listdir(
        path_raw_txt
    ):  # iteramos en la caperta con los ficheros categoria.txt (bad json)
        rows = []
        categorie: str = file.split(".")[0]
        with open(path_raw_txt + file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)  # cargamos diccionarios
                data["categorie"] = categorie
                if type(data["video"]) == list:  # Estaba como lista ahora sera cadena
                    assert len(data["video"]) == 1
                    data["video"] = data["video"][0]
                rows.append(data)  # añadimos

            with open(path_raw_json + file.split(".")[0] + ".json", "w") as json_file:
                json.dump(rows, json_file, indent=3)  # guardamos json limpios
    return


@app.cell
def _(mo):
    mo.md(
        r"""Resulta que el campo `"gloss"` de nuestros datos no se guardo correctamente, para recuperarlo y que se entendible vamos a recuperarlo de la url de la página de donde extrajimos los datos, guardaremos en un dataframe."""
    )
    return


@app.cell
def _(os, path_raw_json: str, pl, urllib):
    dfs = [
        pl.read_json(os.path.join(path_raw_json, p)) for p in os.listdir(path_raw_json)
    ]  # leer todos los json a dataframe
    df = pl.concat(dfs, how="vertical")  # concatenar

    def extract_word(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(parsed.query).get("q", [""])[0]
        return urllib.parse.unquote(q).replace("+", " ")

    # Aplicar con map_elements
    df = df.with_columns(
        df["href"].map_elements(extract_word, return_dtype=pl.Utf8).alias("gloss")
    )  # había problemas con el nombre de las palabras
    return (df,)


@app.cell
def _(mo):
    mo.md(r"""### 4.1 Creación del diccionario""")
    return


@app.cell
def _(df, path_clean: str, pl):
    dictionary = pl.DataFrame(df["gloss"].unique().sort())

    dictionary.write_csv(path_clean + "dictionary.csv")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### 4.2 Corrección del campo `"grammar-categorie"`

    Obtenemos los elementos que si tengan enlace de video y de ellos seleccionamos los que no se haya podido determinar su tipo semántico, en esta caso solo fueron cinco elementos y todos ellos eran nombres, después se formatean todos los nombres en miníscula y sin tíldes.
    """
    )
    return


@app.cell
def _(df):
    videos = df.filter(df["video"] != "no-video")[
        "gloss", "grammar-categorie", "categorie", "video"
    ]  #
    videos.filter(
        videos["grammar-categorie"] == "unknow"
    )  # ver si hay videos sin tipo semántico
    return (videos,)


@app.cell
def _(path_clean: str, pl, unidecode, videos):
    filtered_videos: pl.DataFrame = videos.with_columns(
        videos["grammar-categorie"]
        .replace({"unknow": "Nombre"})
        .alias("grammar-categorie")  # quitar unknow (todos deberían ser nombre)
    )

    filtered_videos = filtered_videos.with_columns(
        filtered_videos["grammar-categorie"]
        .map_elements(str.lower)  # todo en minúsculas
        .map_elements(unidecode)  # Sin tíldes
        .alias("grammar-categorie")  # reemplazar la columna "grammar-categorie"
    )

    filtered_videos.write_csv(path_clean + "sts_videos.csv")
    return (filtered_videos,)


@app.cell
def _(mo):
    mo.md(r"""## 5. Exploración de los datos""")
    return


@app.cell
def _(filtered_videos: "pl.DataFrame", mo):
    mo.ui.data_explorer(filtered_videos)
    return


@app.cell
def _(filtered_videos: "pl.DataFrame", pl):
    categorie_count = filtered_videos.group_by("categorie").agg(pl.len().alias("count"))

    categorie_count = categorie_count.transpose(
        column_names=categorie_count["categorie"].to_list(), include_header=False
    )

    categorie_count
    return


@app.cell
def _(mo):
    mo.md(r"""## 6. Descarga de los videos""")
    return


@app.cell
def _():
    csv_in: str = "data-mining/clean/sts_videos.csv"
    csv_out: str = "data-mining/clean/sts_videos_labeled.csv"
    videos_path: str = "data-mining/videos/"
    return csv_in, csv_out, videos_path


@app.cell
def _(csv_in: str, pl):
    videos_df = pl.read_csv(csv_in)
    return


@app.cell
def _(os, videos_path: str):
    os.makedirs(videos_path, exist_ok=True)
    return


@app.cell
def _():
    FIGURES: int = 5

    class VideoLabeler:
        def __init__(self, id=0) -> None:
            self.id = id

        def get_id(self):
            rep = str(self.id)
            n = FIGURES - len(rep)
            self.id += 1
            return n * "0" + rep + ".mp4"

    return (VideoLabeler,)


@app.cell
def _(VideoLabeler, csv_out: str, df, os, pl, requests, videos_path: str):
    def download_sts_videos():
        vl = VideoLabeler()

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
                    "gloss": row.get("gloss", None),
                    "grammar-categorie": row.get("grammar-categorie", None),
                    "categorie": row.get("categorie", None),
                }
            )

        # Convertimos a polars DataFrame y lo guardamos como CSV
        df_out = pl.DataFrame(records)
        df_out.write_csv(csv_out)

        print(f"CSV generado en: {csv_out}")

    return


if __name__ == "__main__":
    app.run()
