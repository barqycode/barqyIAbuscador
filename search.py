from ddgs import DDGS
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup
from langdetect import detect
import requests
import re
import time

model = SentenceTransformer("all-MiniLM-L6-v2")

# Lista de dominios explícitos para mejorar las búsquedas directas
DOMINIOS_ESPECIALES = [
    "facebook", "instagram", "duolingo", "youtube", "twitter", "linkedin", "github",
    "wikipedia", "pinterest", "netflix", "tiktok", "udemy", "coursera", "reddit",
    "stackoverflow", "bbc", "cnn", "nytimes", "eltiempo", "caracoltv", "medium",
    "tumblr", "vimeo", "imdb", "soundcloud", "bandcamp", "mercadolibre", "aliexpress",
    "amazon", "ebay", "clarin", "infobae", "elpais", "elmundo", "marca", "as",
    "espn", "goal", "crunchyroll", "disneyplus", "hbo", "paramountplus", "blizzard",
    "riotgames", "epicgames", "itch", "mega", "drive.google", "notion.so", "figma", "google"
]

def extraer_texto(url):
    try:
        response = requests.get(url, timeout=5)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        textos = " ".join(p.get_text() for p in soup.find_all("p"))
        return textos.strip()
    except Exception as e:
        print(f"Error al procesar {url}: {e}")
        return ""

def detectar_idioma(texto):
    try:
        return detect(texto)
    except:
        return None

def es_dominio_especial(url):
    return any(dominio in url for dominio in DOMINIOS_ESPECIALES)

def obtener_urls_ddg(consulta, limite=10):
    with DDGS() as ddgs:
        resultados = ddgs.text(consulta, region='wt-wt', safesearch='Moderate', max_results=limite)
        return [r["href"] for r in resultados]
    
def buscar_imagenes(consulta, limite=10):
    with DDGS() as ddgs:
        resultados_img = ddgs.images(consulta, max_results=limite)
        imagenes = [(r["image"], r.get("title", ""), r["source"]) for r in resultados_img]
    return imagenes


def buscar_videos(consulta, limite=10):
    with DDGS() as ddgs:
        resultados = ddgs.text(f"{consulta} site:youtube.com", max_results=limite)
        videos = []
        for r in resultados:
            url = r.get("href", "")
            titulo = r.get("title", "")
            fuente = r.get("source", "")
            imagen = r.get("image", "")
            if "youtube.com/watch" in url:
                videos.append((url, titulo, fuente, imagen))
    return videos

def buscar_con_ia(consulta):
    idioma_consulta = detectar_idioma(consulta)
    urls = obtener_urls_ddg(consulta, limite=15)
    consulta_vec = model.encode(consulta, convert_to_tensor=True)
    resultados = []

    # Si la consulta menciona directamente un dominio especial, añade su URL base
    for dominio in DOMINIOS_ESPECIALES:
        if re.search(rf"\b{re.escape(dominio)}\b", consulta, re.IGNORECASE):
            if "drive.google" in dominio:
                url_directa = "https://drive.google.com"
            elif "notion.so" in dominio:
                url_directa = "https://www.notion.so"
            else:
                url_directa = f"https://www.{dominio}.com"
            resultados.append((1.0, url_directa, f"Enlace directo a {dominio}"))
            break  # solo añadir una vez

    for url in urls:
        if es_dominio_especial(url):
            resultados.append((0.9, url, f"Enlace a sitio conocido: {url}"))
            continue

        texto = extraer_texto(url)
        if texto:
            idioma_texto = detectar_idioma(texto)
            if idioma_texto == idioma_consulta:
                texto_vec = model.encode(texto, convert_to_tensor=True)
                similitud = util.cos_sim(consulta_vec, texto_vec).item()
                resultados.append((similitud, url, texto[:300]))

    return resultados[:10]
