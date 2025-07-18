from flask import Flask, request, render_template
from search import buscar_con_ia, buscar_imagenes, buscar_videos

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    imagenes = []
    videos = []
    consulta = ""
    tipo = "texto"
    if request.method == "POST":
        consulta = request.form["consulta"]
        tipo = request.form.get("tipo", "texto")

        if tipo == "texto":
            resultados = buscar_con_ia(consulta)
        elif tipo == "imagenes":
            imagenes = buscar_imagenes(consulta)
        elif tipo == "videos":
            videos = buscar_videos(consulta)

    return render_template("index.html",
                           consulta=consulta,
                           tipo=tipo,
                           resultados=resultados,
                           imagenes=imagenes,
                           videos=videos)

if __name__ == "__main__":
    app.run(debug=True)
