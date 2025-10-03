import marimo

__generated_with = "0.16.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(rf"""# Scrap de la página web de la `CNSE`""")
    return


@app.cell
def _():
    import requests # para hacer peticiones http simples
    from bs4 import BeautifulSoup # parseo de html
    return BeautifulSoup, requests


@app.cell
def _():
    # Definimos algunas constantes
    cnse_autocomplete_api: str = "https://fundacioncnse-dilse.org/php/buscador-autocompletar_nuevo.php" # url de autocompletado de la LSE
    lse_dictionary_api: str = "https://fundacioncnse.org/educa/bancolse/listado-de-signos.php#gsc.tab=0" # url del diccionario LSE
    return cnse_autocomplete_api, lse_dictionary_api


@app.cell
def _():
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36"
    } # Header para hacer peticiones al servidor del diccionario LSE

    headers_with_json: dict[str, str] = headers # Header para hacer peticiones a la api de autocompletado de LSE
    headers['Acept'] = 'application/json'
    return headers, headers_with_json


@app.cell
def _(
    BeautifulSoup,
    headers: dict[str, str],
    lse_dictionary_api: str,
    requests,
):
    import json
    from unidecode import unidecode

    rep = requests.get(lse_dictionary_api, headers=headers, timeout=1000) # Obtenemos el html del diccionario LSE
    soup = BeautifulSoup(rep.text, "html.parser") # Parseamos html

    ids = ["cat"] + ["cat" + str(i) for i in range(2, 13)]  # Creamos los id's del contenido que nos interesa (cat1 no existe)

    # Recuparemos enlace y texto de las categorias almacenados en los <a/>
    refs = [
        {"href": a["href"], "text": unidecode(a.get_text()).lower()}
        for div in [soup.find("div", id=id) for id in ids]  # recorre los divs
        if div  # solo si existe
        for a in div.find_all("a", href=True)  # recorre los <a> dentro de cada div
    ]

    for r in refs:
        if '/' in r['text']:
            masc, *female = r['text'].split('/') # quitar palabras masculino/femenino
            r['text'] = masc

        if '(' in r['text']:
            masc, *female = r['text'].split('(') # quitar especificación de tipo de palabra
            r['text'] = masc

        if '?' in r['text']:
            r['text'] = r['text'].split('?')[1] # quitar interrogante ?palabra?

        if '!' in r['text']:
            r['text'] = r['text'].split('!')[1] # quitar exclamciones !palabra!


    with open('dict.json', 'w') as j:
        json.dump(refs, j, indent=3)
    return json, refs, unidecode


@app.cell
def _():
    # Extracción del autocompletado usando como prefijo solo el abecedario
    from string import ascii_uppercase as words
    return


@app.cell
def _(cnse_autocomplete_api: str, headers_with_json: dict[str, str], requests):
    # Llamadas a la api de autocompletación

    def autocomplete(query: str):
        params = {"buscar": query}
        r = requests.get(cnse_autocomplete_api, params=params, headers=headers_with_json, timeout=10)
        r.raise_for_status()
        return r.json()
    return (autocomplete,)


@app.cell
def _():
    from trie import Trie
    return (Trie,)


@app.cell
def _(Trie, autocomplete, refs, requests):
    # Llamada a la api de autocompletado con las palabras del diccionario LSE, guardadas eficientemente en un Trie

    def get_lse_words(trie: Trie):
        for ref in refs:
            try:
                text: str = ref['text'] # ya esta en minúsculas
                splits: list[str] = text.split(' ') + [text] # dividimos los espacios incluyendo la misma palabra

                for split in splits:
                    if not trie.contains(split): # no hacemos llamadas innecesarias
                        completions = autocomplete(split)

                        if completions:
                            print(completions)
                            for comp in completions:
                                trie.insert(comp['value']) # añadir palabras

            except requests.HTTPError:
                print(f'Ocurrio un error en la palabra {text}')
    return (get_lse_words,)


@app.cell
def _(Trie):
    # creamos el Trie
    trie: Trie = Trie()
    return (trie,)


@app.cell
def _(get_lse_words, trie: "Trie"):
    get_lse_words(trie)
    return


@app.cell
def _(trie: "Trie"):
    with open('trie.txt', 'w') as f:
        f.write(trie.to_str())
    return


@app.cell
def _(trie: "Trie"):
    lse_words: list[str] = trie.to_str().split()
    len(lse_words)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Scrap de la web `Spread the Sign`""")
    return


@app.cell
def _():
    sts_url: str = 'https://spreadthesign.com' # root de la página original
    sts_categories: str = f'{sts_url}/es.es/search/by-category/' # url de la página de las categorías
    return sts_categories, sts_url


@app.cell
def _(headers: dict[str, str], requests, sts_categories: str):
    sts_categories_page = requests.get(sts_categories, headers=headers) # hmtl de la página de las categorías
    return (sts_categories_page,)


@app.cell
def _(BeautifulSoup, sts_categories_page, unidecode):
    sts_categories_soup = BeautifulSoup(sts_categories_page.text, 'html.parser') # parseamos html de las categorías

    categories = sts_categories_soup.find(id='categories').find_all('li', recursive=False)  # encontramos todas las listas, solo padre

    categories_links = [
        {'href': tag['href'], 'text': unidecode(tag.get_text()).lower()}
        for cat in categories
        for tag in cat.find_all('a', href=True, recursive=False) # Solo el primero no los hijos
    ] # Obtenemos todos los enlace en de las listas en formato {'href': 'referencia', 'text': 'categoria'}

    repeted: set[str] = set() # Creamos un conjunto de categorias no repetidas
    categories_links_filtered = [] # lista con las categorias filtradas

    for cat in categories_links:
        if cat['text'] not in repeted:
            categories_links_filtered.append(cat)
            repeted.add(cat['text'])


    categories_links = categories_links_filtered # Sustituimos la lista filtrada
    categories_links
    return (categories_links,)


@app.function
# '\n        palabra\n        \n          tipo-palabra\n'  ->  {'text': palabra, 'type': tipo-palabra}
def format_text_type(text: str):
    if '\n' not in text:
        return {'text': text, 'type': 'next-page'}

    try:
        _, word, _, wtype, _ = text.split('\n')
        word = word.split(' ')[-1]
        wtype = wtype.split(' ')[-1]
    except (RuntimeError, ValueError):
        return {'text': text, 'type': 'unknow'}

    return {'text': word, 'type': wtype}


@app.cell
def _(BeautifulSoup):
    from collections import deque

    def get_theme_links(soup: BeautifulSoup) -> deque:
        search_row = soup.find(id='search-row')
        theme_links = [{'href': l['href'], 
                       **format_text_type(l.get_text())} 
                       for l in search_row.find_all('a')]


        only_theme_links = [link for link in theme_links if link['type'] != 'next-page'] # todos los enlaces que no son página de siguiente
        next_pages_links = [np for np in theme_links if np['type'] == 'next-page'] # lo enlaces que son de páginas siguiente o previa
        theme_links = only_theme_links

        #print(next_pages_links)

        if len(next_pages_links) > 0:
            theme_links += [next_pages_links[-1]] # Si hay página siguiente cogemos la última que sera la página siguiente

        return deque(theme_links)
    return deque, get_theme_links


@app.class_definition
class bcolors: # Colores !!!
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@app.cell
def _(current_cat):
    global current_cat
    return


@app.cell
def _(
    BeautifulSoup,
    Trie,
    categories_links,
    deque,
    get_theme_links,
    headers: dict[str, str],
    json,
    requests,
    sts_url: str,
):
    import sys # Para la salida de error

    def get_sts_videos():
        visited_next_pages = Trie() # trie para evitar revisitar paginas siguiente
        current_cat = 0
        theme_links = deque()
        try:
            for cat_link in categories_links[16::]: # iteramos sobre todas las cateogrias (Parar si va lento, recuperar por categoria)
                            # hacemos copia de seguridad por cateroría (⚠️ repetidos por categoría)
                file_name = f"{cat_link['text'].replace(' ', '-')}"
                with open(f'{file_name}.txt','w', encoding='utf-8') as file: 
                    print(f'Guardando copia de seguridad en { bcolors.OKGREEN + file_name + bcolors.ENDC}')
                    current_cat += 1 # por seguridad rastreamos en que categoria nos quedamos
                    print(f'Última categoria visitada (índice) {current_cat}')
                
                    current_url: str = f'{sts_url}{cat_link['href']}' # url de la página de categoría actual
                    print(f"Accediendo a la categoria {bcolors.BOLD +  bcolors.UNDERLINE + cat_link['text'] + 
                    bcolors.ENDC} desde {bcolors.OKBLUE + sts_url}{cat_link['href']}" + bcolors.ENDC)

                    category_page = requests.get(current_url, headers=headers) # obtenemos el html de la página de la categoría
                    category_soup = BeautifulSoup(category_page.text, 'html.parser') # parseamos html de la página

                    theme_links.extend(get_theme_links(category_soup)) # obtenemos todos los enlaces de la página

                    while theme_links:
                        theme = theme_links.popleft() # sacamos un enlace de la cola

                        is_theme_page: bool = theme['type'] != 'next-page' # saber si es una temática o una página siguiente
                        page_url: str = f'{sts_url if is_theme_page else current_url}{theme['href']}' # url correcto para la página

                        page = requests.get(page_url, headers=headers) # obtenemos la página a partir del enlace
                        page_soup = BeautifulSoup(page.text, 'html.parser') # parseamos hmtl de la página

                        if is_theme_page:
                            print(f"Accediendo a la temática {theme['text']}")

                            video = page_soup.find_all('video') # buscar videos
                            if not video:
                                print(f"No hay video para {theme['text']}", file=sys.stderr)
                                theme['video'] = 'no-video' # si no hay video lo especificamos

                            else:
                                theme['video'] = [src['src'] for src in video] # guardamos todos los videos (al menos uno)

                            stringified = json.dumps(theme) # convertimos a cadena
                            file.write(stringified + '\n')

                        else:
                            if not visited_next_pages.contains(page_url):
                                next_theme_links: deque = get_theme_links(page_soup) # obtenemos todos los enlaces de la siguiente página
                                #print(next_theme_links)
                                print(f"Añadiendo la siguiente página desde {bcolors.OKBLUE + bcolors.UNDERLINE + page_url + bcolors.ENDC}")
                                theme_links.extend(next_theme_links) # añadimos a la cola
                                visited_next_pages.insert(page_url)

        except (RuntimeError, ValueError):
            print("Error", file=sys.stderr)
            return current_cat
        return current_cat

    return (get_sts_videos,)


@app.cell
def _(get_sts_videos):
    backup = get_sts_videos()
    return


if __name__ == "__main__":
    app.run()
