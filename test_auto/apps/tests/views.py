from django.shortcuts import render
from django.http import HttpResponse
from test_auto.settings import JSONS_DATA_PATH
from pathlib import Path
import json
from django.http import Http404
from django.http import JsonResponse
from .models import RespuestaTest
from django.shortcuts import redirect


# Create your views here.

def load_preguntas(test) -> list:
    """
    Carga las preguntas de un test desde un archivo JSON.
    Salida: 
    - Lista de preguntas (diccionarios)
    Cada pregunta es un diccionario con las claves:
    - numeroPregunta: int
    - pregunta: str
    - respuestas: list de dict { numero: str, texto: str }
    - respuestaCorrecta: int (índice de la opción correcta)
    - practica: bool (opcional)
    - imagen: str = (nombre del archivo de imagen asociado a la pregunta).jpg
    Si el archivo no existe, lanza Http404
    """
    ruta = JSONS_DATA_PATH / "tests" / f"{test}.json"
    if not ruta.exists():
        raise Http404("Test no encontrado")

    with open(ruta, encoding="utf-8") as f:
        preguntas = json.load(f)
        
    # Añadir a cada pregunta un campo imagen con el numero de la pregunta
    for pregunta in preguntas:
        pregunta["imagen"] = f"{pregunta['numeroPregunta']}.jpg"
        
    # quitar los jsons que no tengan la clave "practica"= true
    preguntas = [p for p in preguntas if p.get("practica", False)]

    return preguntas


def list(request):
    # listar los archivos JSON en el directorio especificado JSONS_DATA_PATH / tests ordenados por nombre
    tests_dir = JSONS_DATA_PATH / "tests"
    tests_files = sorted(tests_dir.glob("*.json"), key=lambda f: f.name)
    
    # quitar la extensión .json de los nombres de los archivos
    tests_files = [f.with_suffix('') for f in tests_files]
    
    # Crear una lista con los nombres de los tests, un campo desaprobado si tienen mas de 3 respuestas incorrectas
    tests = []
    for test_file in tests_files:
        test = {
            "name": test_file.name,
        }
        
        # obtener las preguntas del test de los json
        preguntas = load_preguntas(test_file)
        cant_preguntas = len(preguntas)
        
        # obtener las respuestas del test de la base de datos
        respuestasTest = RespuestaTest.objects.filter(test=test_file.name)
        cant_respuestas = respuestasTest.count()

        incorrectas = 0
        for pregunta in preguntas:
            respuesta = respuestasTest.filter(pregunta_numero=pregunta["numeroPregunta"]).only("respuesta_seleccionada").first()
            if respuesta and str(respuesta.respuesta_seleccionada) != str(pregunta["respuestaCorrecta"]):
                incorrectas += 1
        
        if cant_preguntas == 0:
            test['estado'] = 'no_disponible'
        elif cant_respuestas == 0:
            test['estado'] = 'sin_hacer'
        elif cant_respuestas < cant_preguntas:
            test['estado'] = 'incompleto'
        else:
            if incorrectas > 3:
                test['estado'] = 'desaprobado'
            else:
                test['estado'] = 'aprobado'
                
        tests.append(test)

    return render(request, 'tests/listado.html', {'tests': tests})


def pregunta_view(request, test, numero):
    print(f"Ver Pregunta. Test: {test}, Pregunta: {numero}")
    
    preguntas = load_preguntas(test)
    total_preguntas = len(preguntas)
    print(f"Preguntas cargadas: {total_preguntas}")
    
    respuestasTest = RespuestaTest.objects.filter(test=test)
    cant_respuestas = respuestasTest.count()
        
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
        
    # Verificar en la base de datos si hay una respuesta guardada para este test y pregunta
    # Si existe, preseleccionar la respuesta guardada
    # Si no existe, preseleccionar 0
    preselected = 0
    try:
        respuesta = RespuestaTest.objects.get(test=test, pregunta_numero=numero)
        preselected = respuesta.respuesta_seleccionada
    except RespuestaTest.DoesNotExist:
        preselected = 0

    contexto = {
        "pregunta": pregunta,
        "numero": numero,
        "indice": indice,
        "total": len(preguntas),
        "test": test,
        "preselected": preselected,
        "numeroPreguntaAnterior": numeroPreguntaAnterior,
        "numeroPreguntaSiguiente": numeroPreguntaSiguiente,
        "total_preguntas": total_preguntas,
        "cant_respuestas": cant_respuestas,
        "completado": completado,
    }
    print(f"contexto: {contexto}")
    
    return render(request, "tests/pregunta.html", contexto)


def registrar_respuesta(request):
    if request.method == "POST":
        test = request.POST.get("test")
        pregunta = request.POST.get("pregunta")
        seleccionada = request.POST.get("seleccionada")
        
        # Aquí puedes guardar en sesión, base de datos, etc.
        print(f"Registrar Respuesta. Test: {test}, Pregunta: {pregunta}, Seleccionada: {seleccionada}")
        
        # Guardar la respuesta en la base de datos
        # buscar si ya existe una respuesta para este test y pregunta
        try:
            respuesta = RespuestaTest.objects.get(test=test, pregunta_numero=pregunta)
            respuesta.respuesta_seleccionada = seleccionada
            respuesta.save()
        except RespuestaTest.DoesNotExist:
            respuesta = RespuestaTest(
                test=test,
                pregunta_numero=pregunta,
                respuesta_seleccionada=seleccionada
            )
            respuesta.save()
            
        preguntas = load_preguntas(test)
        total_preguntas = len(preguntas)
        
        respuestasTest = RespuestaTest.objects.filter(test=test)
        cant_respuestas = respuestasTest.count()
        
        completado = total_preguntas == cant_respuestas

        return JsonResponse({"status": "ok", "test": test, "pregunta": pregunta, "seleccionada": seleccionada, "completado": completado})
    return JsonResponse({"error": "Método no permitido"}, status=405)


def clean_respuestas(request, test):
    """
    Elimina todas las respuestas guardadas en la base de datos.
    y redirige a la vista a la pregunta 0 del test "test"
    """
    
    # Eliminar todas las respuestas del test especificado
    RespuestaTest.objects.filter(test=test).delete()

    return redirect('tests:pregunta_view', test=test, numero=1) # Redirigir a la pregunta 1 del test "test"


def resultado_view(request, test):
    """
    Muestra el resultado del test.
    """
    preguntas = load_preguntas(test)
    total_preguntas = len(preguntas)
    
    respuestasTest = RespuestaTest.objects.filter(test=test)
    cant_respuestas = respuestasTest.count()
    
    correctas = 0
    incorrectas = 0
    for pregunta in preguntas:
        respuesta = respuestasTest.filter(pregunta_numero=pregunta["numeroPregunta"]).only("respuesta_seleccionada").first()

        if respuesta:
            if str(respuesta.respuesta_seleccionada) == str(pregunta["respuestaCorrecta"]):
                correctas += 1
            else:
                incorrectas += 1
    
    aprobada = incorrectas <= 3 and cant_respuestas == total_preguntas
    
    contexto = {
        "test": test,
        "total_preguntas": total_preguntas,
        "cant_respuestas": cant_respuestas,
        "correctas": correctas,
        "incorrectas": incorrectas,
        "aprobada": aprobada,
    }
    print(f"contexto: {contexto}")
    
    return render(request, "tests/resultado.html", contexto)