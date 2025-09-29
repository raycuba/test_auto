from django.shortcuts import render
from django.http import HttpResponse
from test_auto.settings import JSONS_DATA_PATH
from pathlib import Path
import json
from django.http import Http404
from django.http import JsonResponse
from .models import RespuestaExamen
from django.shortcuts import redirect


# Create your views here.

def list(request):
    
    # listar los archivos JSON en el directorio especificado JSONS_DATA_PATH / examenes ordenados por nombre
    examenes_dir = JSONS_DATA_PATH / "examenes"
    examenes_files = sorted(examenes_dir.glob("*.json"), key=lambda f: f.name)
    
    # quitar la extensión .json de los nombres de los archivos
    examenes_files = [f.with_suffix('') for f in examenes_files]

    return render(request, 'examenes/listado.html', {'examenes': examenes_files})


def pregunta_view(request, examen, numero):
    print(f"Ver Pregunta. Examen: {examen}, Pregunta: {numero}")
    
    ruta = JSONS_DATA_PATH / "examenes" / f"{examen}.json"
    if not ruta.exists():
        raise Http404("Examen no encontrado")

    with open(ruta, encoding="utf-8") as f:
        preguntas = json.load(f)
        
    # Añadir a cada pregunta un campo imagen con el numero de la pregunta
    preguntas = [{**p, "imagen": f"{i+1}.png"} for i, p in enumerate(preguntas)]
        
    # quitar los jsons que no tengan la clave "practica"= true
    preguntas = [p for p in preguntas if p.get("practica", False)]
    
    # Verificar en la base de datos si hay una respuesta guardada para este examen y pregunta
    # Si existe, preseleccionar la respuesta guardada
    # Si no existe, preseleccionar 0
    preselected = 0
    try:
        respuesta = RespuestaExamen.objects.get(examen=examen, pregunta_numero=numero)
        preselected = respuesta.respuesta_seleccionada
    except RespuestaExamen.DoesNotExist:
        preselected = 0

    try:
        pregunta = preguntas[numero-1]  # Restar 1 para índice basado en 0
    except IndexError:
        raise Http404("Pregunta no disponible")
    
    print(pregunta)
    print(preselected)

    contexto = {
        "pregunta": pregunta,
        "numero": numero,
        "total": len(preguntas),
        "examen": examen,
        "preselected": preselected,
    }
    return render(request, "examenes/pregunta.html", contexto)


def registrar_respuesta(request):
    if request.method == "POST":
        examen = request.POST.get("examen")
        pregunta = request.POST.get("pregunta")
        seleccionada = request.POST.get("seleccionada")
        
        # Aquí puedes guardar en sesión, base de datos, etc.
        print(f"Registrar Respuesta. Examen: {examen}, Pregunta: {pregunta}, Seleccionada: {seleccionada}")
        
        # Guardar la respuesta en la base de datos
        # buscar si ya existe una respuesta para este examen y pregunta
        try:
            respuesta = RespuestaExamen.objects.get(examen=examen, pregunta_numero=pregunta)
            respuesta.respuesta_seleccionada = seleccionada
            respuesta.save()
        except RespuestaExamen.DoesNotExist:
            respuesta = RespuestaExamen(
                examen=examen,
                pregunta_numero=pregunta,
                respuesta_seleccionada=seleccionada
            )
            respuesta.save()

        return JsonResponse({"status": "ok", "examen": examen, "pregunta": pregunta, "seleccionada": seleccionada})
    return JsonResponse({"error": "Método no permitido"}, status=405)

def clean_respuestas(request, examen):
    """
    Elimina todas las respuestas guardadas en la base de datos.
    y redirige a la vista a la pregunta 0 del examen "test"
    """
    
    # Eliminar todas las respuestas del examen especificado
    RespuestaExamen.objects.filter(examen=examen).delete()

    return redirect('examenes:pregunta_view', examen=examen, numero=1) # Redirigir a la pregunta 1 del examen "test"



