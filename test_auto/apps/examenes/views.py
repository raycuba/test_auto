from django.shortcuts import render
from django.http import HttpResponse
from config.base import JSONS_DATA_PATH
from pathlib import Path
import json
from django.http import Http404
from django.http import JsonResponse
from .models import RespuestaExamen
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Create your views here.

def load_preguntas(examen) -> list:
    """
    Carga las preguntas de un examen desde un archivo JSON.
    Salida: 
    - Lista de preguntas (diccionarios)
    Cada pregunta es un diccionario con las claves:
    - numeroPregunta: int
    - pregunta: str
    - respuestas: list de dict { numero: str, texto: str }
    - respuestaCorrecta: int (índice de la opción correcta)
    - practica: bool (opcional)
    - imagen: str = (nombre del archivo de imagen asociado a la pregunta).png
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


@login_required
def list(request):
    # usuario logueado
    logged_user = request.user
    
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
        respuestasExamen = RespuestaExamen.objects.filter(user=logged_user, examen=examen_file.name)
        cant_respuestas = respuestasExamen.count()

        incorrectas = 0
        for pregunta in preguntas:
            respuesta = respuestasExamen.filter(pregunta_numero=pregunta["numeroPregunta"]).only("respuesta_seleccionada").first()
            if respuesta and str(respuesta.respuesta_seleccionada) != str(pregunta["respuestaCorrecta"]):
                incorrectas += 1
        
        if cant_preguntas == 0:
            examen['estado'] = 'no_disponible'
        elif cant_respuestas == 0:
            examen['estado'] = 'sin_hacer'
        elif cant_respuestas < cant_preguntas:
            examen['estado'] = 'parcial'
        else:
            if incorrectas > 3:
                examen['estado'] = 'reprobado'
            elif incorrectas == 0:
                examen['estado'] = 'excelente'
            else:
                examen['estado'] = 'aprobado'
                
        examenes.append(examen)

    return render(request, 'examenes/listado.html', {'examenes': examenes})


@login_required
def pregunta_view(request, examen, numero):
    # usuario logueado
    logged_user = request.user

    preguntas = load_preguntas(examen)
    total_preguntas = len(preguntas)

    respuestasExamen = RespuestaExamen.objects.filter(user=logged_user, examen=examen)
    cant_respuestas = respuestasExamen.count()
        
    numeroPreguntaAnterior = None
    numeroPreguntaSiguiente = None

    try:
        if numero == 0:
            pregunta = preguntas[0]  # Primera pregunta
            numero = pregunta["numeroPregunta"]
        else:
            #buscar la pregunta con numeroPregunta == numero
            pregunta = next(p for p in preguntas if p["numeroPregunta"] == numero)
            
        #deteriminar el índice de la pregunta en la lista
        indice = preguntas.index(pregunta)

        numeroPreguntaAnterior = preguntas[indice - 1]['numeroPregunta'] if indice > 0 else None
        numeroPreguntaSiguiente = preguntas[indice + 1]['numeroPregunta'] if indice < len(preguntas) - 1 else None

    except IndexError:
        raise Http404("Pregunta no disponible")
    
    if numeroPreguntaSiguiente is None:
        completado = total_preguntas == cant_respuestas
    else:
        completado = False
        
    # Verificar en la base de datos si hay una respuesta guardada para este examen y pregunta
    # Si existe, preseleccionar la respuesta guardada
    # Si no existe, preseleccionar 0
    preselected = 0
    try:
        respuesta = RespuestaExamen.objects.get(user=logged_user, examen=examen, pregunta_numero=numero)
        preselected = respuesta.respuesta_seleccionada
    except RespuestaExamen.DoesNotExist:
        preselected = 0

    contexto = {
        "pregunta": pregunta,
        "numero": numero,
        "indice": indice,
        "total": len(preguntas),
        "examen": examen,
        "preselected": preselected,
        "numeroPreguntaAnterior": numeroPreguntaAnterior,
        "numeroPreguntaSiguiente": numeroPreguntaSiguiente,
        "total_preguntas": total_preguntas,
        "cant_respuestas": cant_respuestas,
        "completado": completado,
    }
    print(f"contexto: {contexto}")
    
    return render(request, "examenes/pregunta.html", contexto)


@login_required
def registrar_respuesta(request):
    # usuario logueado
    logged_user = request.user
    
    if request.method == "POST":
        examen = request.POST.get("examen")
        pregunta = request.POST.get("pregunta")
        seleccionada = request.POST.get("seleccionada")
        
        # Aquí puedes guardar en sesión, base de datos, etc.
        print(f"Registrar Respuesta. Examen: {examen}, Pregunta: {pregunta}, Seleccionada: {seleccionada}")
        
        # Guardar la respuesta en la base de datos
        # buscar si ya existe una respuesta para este examen y pregunta
        try:
            respuesta = RespuestaExamen.objects.get(user=logged_user, examen=examen, pregunta_numero=pregunta)
            respuesta.respuesta_seleccionada = seleccionada
            respuesta.save()
        except RespuestaExamen.DoesNotExist:
            respuesta = RespuestaExamen(
                user=logged_user,
                examen=examen,
                pregunta_numero=pregunta,
                respuesta_seleccionada=seleccionada
            )
            respuesta.save()
            
        preguntas = load_preguntas(examen)
        total_preguntas = len(preguntas)

        respuestasExamen = RespuestaExamen.objects.filter(user=logged_user, examen=examen)
        cant_respuestas = respuestasExamen.count()
        
        completado = total_preguntas == cant_respuestas

        return JsonResponse({"status": "ok", "examen": examen, "pregunta": pregunta, "seleccionada": seleccionada, "completado": completado})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@login_required
def clean_respuestas(request, examen):
    """
    Elimina todas las respuestas guardadas en la base de datos.
    y redirige a la vista a la pregunta 0 del examen "test"
    """
    
    # usuario logueado
    logged_user = request.user
    
    # Eliminar todas las respuestas del examen especificado
    RespuestaExamen.objects.filter(user=logged_user, examen=examen).delete()

    return redirect('examenes:pregunta_view', examen=examen, numero=1) # Redirigir a la pregunta 1 del examen "test"


@login_required
def resultado_view(request, examen):
    """
    Muestra el resultado del examen.
    """
    # usuario logueado
    logged_user = request.user
    
    preguntas = load_preguntas(examen)
    total_preguntas = len(preguntas)

    respuestasExamen = RespuestaExamen.objects.filter(user=logged_user, examen=examen)
    cant_respuestas = respuestasExamen.count()
    
    correctas = 0
    incorrectas = 0
    for pregunta in preguntas:
        respuesta = respuestasExamen.filter(pregunta_numero=pregunta["numeroPregunta"]).only("respuesta_seleccionada").first()

        if respuesta:
            if str(respuesta.respuesta_seleccionada) == str(pregunta["respuestaCorrecta"]):
                correctas += 1
            else:
                incorrectas += 1
    
    if cant_respuestas != total_preguntas:
        estado = 'parcial'
    elif incorrectas > 3:
        estado = 'reprobado'
    elif incorrectas == 0:
        estado = 'excelente'
    else:
        estado = 'aprobado'
    
    contexto = {
        "examen": examen,
        "total_preguntas": total_preguntas,
        "cant_respuestas": cant_respuestas,
        "correctas": correctas,
        "incorrectas": incorrectas,
        "estado": estado,
    }
    print(f"contexto: {contexto}")
    
    return render(request, "examenes/resultado.html", contexto)