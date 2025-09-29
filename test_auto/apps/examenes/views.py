from django.shortcuts import render
from django.http import HttpResponse
from test_auto.settings import JSONS_DATA_PATH
from pathlib import Path
import json
from django.http import Http404
from django.http import JsonResponse



# Create your views here.

def list(request):
    
    # listar los archivos JSON en el directorio especificado JSONS_DATA_PATH / examenes ordenados por nombre
    examenes_dir = JSONS_DATA_PATH / "examenes"
    examenes_files = sorted(examenes_dir.glob("*.json"), key=lambda f: f.name)
    
    # quitar la extensión .json de los nombres de los archivos
    examenes_files = [f.with_suffix('') for f in examenes_files]

    return render(request, 'examenes/listado.html', {'examenes': examenes_files})


def pregunta_view(request, examen, numero):
    ruta = JSONS_DATA_PATH / "examenes" / f"{examen}.json"
    if not ruta.exists():
        raise Http404("Examen no encontrado")

    with open(ruta, encoding="utf-8") as f:
        preguntas = json.load(f)
        
    # Añadir a cada pregunta un campo imagen con el numero de la pregunta
    preguntas = [{**p, "imagen": f"{i+1}.png"} for i, p in enumerate(preguntas)]
        
    # quitar los jsons que no tengan la clave "practica"= true
    preguntas = [p for p in preguntas if p.get("practica", False)]

    try:
        pregunta = preguntas[numero]
    except IndexError:
        raise Http404("Pregunta no disponible")

    contexto = {
        "pregunta": pregunta,
        "numero": numero,
        "total": len(preguntas),
        "examen": examen,
        "preselected": 1,
    }
    return render(request, "examenes/pregunta.html", contexto)


def registrar_respuesta(request):
    if request.method == "POST":
        examen = request.POST.get("examen")
        pregunta = request.POST.get("pregunta")
        seleccionada = request.POST.get("seleccionada")
        
        # Aquí puedes guardar en sesión, base de datos, etc.
        print(f"Examen: {examen}, Pregunta: {pregunta}, Seleccionada: {seleccionada}")
        
        return JsonResponse({"status": "ok", "examen": examen, "pregunta": pregunta, "seleccionada": seleccionada})
    return JsonResponse({"error": "Método no permitido"}, status=405)



