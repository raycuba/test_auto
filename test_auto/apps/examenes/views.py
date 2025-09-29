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

def load_preguntas(examen) -> list:
    """
    Carga las preguntas de un examen desde un archivo JSON.
    Salida: 
    - Lista de preguntas (diccionarios)
    Cada pregunta es un diccionario con las claves:
    - numero: int
    - pregunta: str
    - opciones: list de str
    - correcta: int (índice de la opción correcta)
    - practica: bool (opcional)
    - imagen: str (nombre del archivo de imagen asociado a la pregunta)
    Si el archivo no existe, lanza Http404
    """
    ruta = JSONS_DATA_PATH / "examenes" / f"{examen}.json"
    if not ruta.exists():
        raise Http404("Examen no encontrado")

    with open(ruta, encoding="utf-8") as f:
        preguntas = json.load(f)
        
    # Añadir a cada pregunta un campo imagen con el numero de la pregunta
    for pregunta in preguntas:
        pregunta["imagen"] = f"{pregunta['numeroPregunta']}.png"
        
    # quitar los jsons que no tengan la clave "practica"= true
    preguntas = [p for p in preguntas if p.get("practica", False)]
    
    return preguntas


def list(request):
    # listar los archivos JSON en el directorio especificado JSONS_DATA_PATH / examenes ordenados por nombre
    examenes_dir = JSONS_DATA_PATH / "examenes"
    examenes_files = sorted(examenes_dir.glob("*.json"), key=lambda f: f.name)
    
    # quitar la extensión .json de los nombres de los archivos
    examenes_files = [f.with_suffix('') for f in examenes_files]
    
    # Crear una lista con los nombres de los examenes, un campo desaprobado si tienen mas de 3 respuestas incorrectas
    examenes = []
    for examen_file in examenes_files:
        examen = {
            "name": examen_file.name,
        }
        
        # obtener las preguntas del examen de los json
        preguntas = load_preguntas(examen_file)
        cant_preguntas = len(preguntas)
        
        # obtener las respuestas del examen de la base de datos
        respuestas = RespuestaExamen.objects.filter(examen=examen_file.name)
        cant_respuestas = respuestas.count()
    
        incorrectas = 0
        index = 0
        for pregunta in preguntas:
            respuesta = respuestas.filter(pregunta_numero=index).only("respuesta_seleccionada").first()
            if respuesta and respuesta.respuesta_seleccionada != str(pregunta["respuestaCorrecta"]):
                incorrectas += 1
                
            index += 1
        
        if cant_respuestas == 0:
            examen['estado'] = 'sin_hacer'
        elif cant_respuestas < cant_preguntas:
            examen['estado'] = 'incompleto'
        else:
            if incorrectas > 3:
                examen['estado'] = 'desaprobado'
            else:
                examen['estado'] = 'aprobado'
                
        examenes.append(examen)

    return render(request, 'examenes/listado.html', {'examenes': examenes})


def pregunta_view(request, examen, numero):
    print(f"Ver Pregunta. Examen: {examen}, Pregunta: {numero}")
    
    preguntas = load_preguntas(examen)
    
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



