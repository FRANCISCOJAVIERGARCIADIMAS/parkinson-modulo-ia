import pandas as pd
from sklearn.tree import DecisionTreeClassifier, _tree
from flask import Flask, jsonify, request
from sklearn.tree import export_text
from sklearn import metrics
from joblib import dump, load
import os.path
from sklearn.tree import export_graphviz
# import graphviz
from flask import Flask
from flask_cors import CORS
import requests
import json
# from twilio.rest import Client

# Mysql
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE'])

port = int(os.environ.get('PORT', 7291))
print("PORT RAIL:", port )
# leer el archivo CSV de entrenamiento
data = pd.read_csv("training-2.csv")

# preparar los datos
X = data.drop('status', axis=1)
y = data['status']  

# nombre del archivo donde se guardará el modelo
# filename = 'tree.joblib'

# si el archivo no existe, entrenar el árbol de decisión y guardarlo
# if not os.path.isfile(filename):
#     dtc = DecisionTreeClassifier(max_depth=6, min_samples_leaf=1)
#     dtc.fit(X, y)
#     dump(dtc, filename)
    
# cargar el árbol de decisión desde el archivo
dtc = load('tree.joblib')


# leer el archivo CSV de prueba
test_data = pd.read_csv("test-2.csv")

# preparar los datos de prueba
X_test = test_data.drop('status', axis=1)
y_test = test_data['status']

# predecir los valores de la prueba
y_pred = dtc.predict(X_test)

# evaluar el modelo
print("Exactitud:",metrics.accuracy_score(y_test, y_pred))

# generar una representación de texto del árbol generado
tree_rules = export_text(dtc, feature_names=X.columns.tolist())


# exportar el árbol de decisión en formato Graphviz
# dot_data = export_graphviz(dtc, out_file=None, filled=True, rounded=True,
#                                 feature_names=X.columns.tolist(),
#                                 class_names=['Parkinson', 'Sano'])
# graph = graphviz.Source(dot_data)

# ================================= DEFAULT =====================================

# @app.route('/mi-ruta')
# def mi_vista():
#     print(tree_rules)
#     graph.render('arbol', format='png')
#     return jsonify({"Hola": "mundo!"})


@app.route('/hola-mundo')
def hola_mundo():
    return jsonify({"Hola": "mundo!"})

@app.route("/")
def index():
    return "<h1>Hello!</h1>"

# Arbol con id Terminales
# @app.route('/tree-tag')
# def tree_tag():
#     print_tree(dtc, X.columns.tolist())
#     # print(tree_rules)
#     return jsonify({"tree": "tag"})


# generar una representación de texto del árbol generado, agregando "(TERMINAL)" y el identificador de nodo a los nodos terminales
# def print_tree(dtc, feature_names):
#     r = export_text(dtc, feature_names=feature_names).split('\n')
#     new_r = []
#     node_id = 0
#     for s in r:
#         if s.strip():
#             if 'class' in s:
#                 s = s.replace('class', f'class (TERMINAL, {node_id})')
#                 node_id += 1
#             else:
#                 s = f'[{node_id}] {s}'
#                 node_id += 1
#             new_r.append(s)
#     print("\n".join(new_r))



# ============================== VOZ ===========================

# IA
@app.route('/voz/asignar', methods=['POST'])
def predecir():
    # Obtener los valores del registro de prueba
    registro = request.json

    # Crear un nuevo DataFrame con el registro de prueba
    registro_df = pd.DataFrame(registro, index=[0])

    # Usar el modelo para predecir la variable de clase del registro
    predicted_class = dtc.predict(registro_df)

    # Definir la función para imprimir las condiciones de los nodos visitados por el registro
    def get_decision_path(dtc, registro):
        # Obtener el índice de la fila del registro
        idx = registro.index[0]

        # Obtener la matriz sparse de decision_path para el registro
        decision_path = dtc.decision_path(registro)

        # Obtener el árbol de decisión
        tree = dtc.tree_

        # Obtener las condiciones de los nodos visitados por el registro
        condiciones = []
        for node_id in decision_path.indices:
            # Obtener el índice de la variable utilizada en este nodo
            feature_index = tree.feature[node_id]
            if feature_index == _tree.TREE_UNDEFINED:
                continue
            feature_name = X.columns[feature_index]

            # Obtener el valor de umbral utilizado en este nodo
            threshold = tree.threshold[node_id]

            # Obtener el valor del registro para la variable utilizada en este nodo
            value = registro[feature_name].iloc[0]

            # Guardar la condición del nodo
            if value <= threshold:
                condiciones.append(f"{feature_name} <= {threshold}")
            else:
                condiciones.append(f"{feature_name} > {threshold}")
        
        return predicted_class[0], condiciones

    # Obtener la predicción y las condiciones
    predicted_class, condiciones = get_decision_path(dtc, registro_df)

    

    # Crear el diccionario de respuesta
    respuesta = {
        'registro':registro,
        'predicted_class': predicted_class,
        'condiciones': condiciones,
        'result': evaluar_condiciones_voz(condiciones)
    }
    print("respuesta: ", condiciones)

    resultado = evaluar_condiciones_voz(condiciones)
    
    idM = resultado['idM']
    title = resultado['title']
    type = resultado['type']
    msg = resultado['msg']

    enviar_notificacion(type, title, msg)
    insertar_registro(idM, 3, 2)
    # enviar_whatsapp()
    return jsonify(respuesta)


# Mensajes
def evaluar_condiciones_voz(lista):
    recomendacion_1 = ["PPE <= 0.133993498980999", "MDVP:Fo(Hz) > 192.2729949951172"]
    recomendacion_2 = ["PPE > 0.133993498980999", "spread1 <= -6.736269950866699"]
    recomendacion_3 = ["PPE <= 0.133993498980999", "MDVP:Fo(Hz) <= 192.2729949951172", "MDVP:Flo(Hz) <= 123.05800247192383", "spread1 > -6.832795143127441"]
    recomendacion_4 = ["PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) <= 116.53200149536133", "PPE <= 0.1845259964466095", "MDVP:Fo(Hz) > 109.0354995727539"]
    alerta_1 = ["PPE <= 0.133993498980999", "MDVP:Fo(Hz) <= 192.2729949951172", "MDVP:Flo(Hz) > 123.05800247192383"]
    alerta_2 = ["PPE <= 0.133993498980999", "MDVP:Fo(Hz) <= 192.2729949951172", "MDVP:Flo(Hz) <= 123.05800247192383", "spread1 <= -6.832795143127441"]
    alerta_3 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) > 116.53200149536133", "MDVP:Fo(Hz) <= 195.29949951171875" ]
    alerta_4 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) <= 116.53200149536133", "PPE <= 0.1845259964466095", "MDVP:Fo(Hz) <= 109.0354995727539" ]
    notificacion_1 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) <= 116.53200149536133", "PPE > 0.1845259964466095", "MDVP:Fo(Hz) > 116.21800231933594" ]
    notificacion_2 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) > 116.53200149536133", "MDVP:Fo(Hz) > 195.29949951171875", "MDVP:Fo(Hz) <= 197.84249877929688" ]
    notificacion_3 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) <= 116.53200149536133", "PPE > 0.1845259964466095", "MDVP:Fo(Hz) <= 116.21800231933594" ]
    notificacion_4 = [ "PPE > 0.133993498980999", "spread1 > -6.736269950866699", "MDVP:Fo(Hz) > 116.53200149536133", "MDVP:Fo(Hz) > 195.29949951171875", "MDVP:Fo(Hz) > 197.84249877929688" ]

    
    if all(condicion in lista for condicion in recomendacion_1):
         return {"idM": 4, "title": "🟢 Hidratación", "type": "Recomendación", "msg": "🟢! Tip importante !, recuerda siempre mantener una buena hidratación para ayudar a prevenir el estreñimiento y otros problemas de salud."}
        # return "🟢! Tip importante !, recuerda siempre mantener una buena hidratación para ayudar a prevenir el estreñimiento y otros problemas de salud."
    elif all(condicion in lista for condicion in recomendacion_2):
        return {"idM": 2, "title": "🟢 Bocados pequeños", "type": "Recomendación", "msg": "🟢 Una recomendación útil es que, al comer, tomes pequeños bocados y mastiques bien antes de tragarlos, hazlo con calma esto te ayuda a disminuir el riesgo de atragantamiento."}
    elif all(condicion in lista for condicion in recomendacion_3):
        return {"idM": 3, "title": "🟢 Respiración controlada", "type": "Recomendación", "msg": "🟢 Una idea que te ayudará es realizar ejercicios de respiración controlada para mantener tu capacidad de retener el aire al hablar, ya que la variación en tu frecuencia de voz es normal."}
    elif all(condicion in lista for condicion in recomendacion_4):
        return {"idM": 1, "title": "🟢 Vocalizaciones", "type": "Recomendación", "msg": "🟢 Un consejo práctico es hacer ejercicios para mejorar tu pronunciación y vocalización, esto te ayudará a mantener una buena comunicación con los demás."}
    elif all(condicion in lista for condicion in notificacion_1 ):
        return {"idM": 5, "title": "🟡 Praxias bucofaciales", "type": "Notificación", "msg": "🟡 Le sugerimos seguir practicando los ejercicios de movimiento de los músculos faciales para mantener una buena coordinación al hablar, ya que su frecuencia de voz es normal."}
    elif all(condicion in lista for condicion in notificacion_2 ):
        return {"idM": 8, "title": "🟡 Gimnasia orofacial", "type": "Notificación", "msg": "🟡 Te sugerimos hacer ejercicios de gimnasia para la boca, ya que se detectó que hay un pequeño cambio en tu forma de hablar. Esto te ayudará a mejorar la claridad de tus palabras."}
    elif all(condicion in lista for condicion in notificacion_3 ):
        return {"idM": 7, "title": "🟡 Articulación al hablar", "type": "Notificación", "msg": "🟡 Se detectó un pequeño cambio en tu voz, una recomendación útil es realizar ejercicios para mejorar la movilidad de la boca y tener un mejor control al hablar."}    
    elif all(condicion in lista for condicion in notificacion_4 ):
        return {"idM": 6, "title": "🟡 Ejercicios de lectura", "type": "Notificación", "msg": "🟡 Le sugerimos practicar la lectura en voz alta para mejorar la claridad de su pronunciación, ya que se detectó una leve alteración en la variación de su frecuencia de voz."}
    elif all(condicion in lista for condicion in alerta_1): 
        return {"idM": 11, "title": "🔴 Movimientos linguales", "type": "Alerta", "msg": "🔴 La variación de su frecuencia de voz está un poco alterada, se aconseja aumentar los ejercicios de movimientos linguales."}    
    elif all(condicion in lista for condicion in alerta_2):
        return {"idM": 9, "title": "🔴 Movimiento de boca", "type": "Alerta", "msg": "🔴 Te sugerimos hacer más ejercicios que involucren tus labios y lengua para mejorar la claridad de tu voz al hablar, ya que se detectó que hay una leve diferencia en la forma en que modulas."}
    elif all(condicion in lista for condicion in alerta_3):
        return {"idM": 10, "title": "🔴 Respiración controlada nivel 2", "type": "Alerta", "msg": "🔴 Su forma de hablar podría mejorar, sería bueno que realice más ejercicios para controlar su respiración al hablar."}
    elif all(condicion in lista for condicion in alerta_4):
        return {"idM": 12, "title": "🔴 Dificultad para beber agua", "type": "Alerta", "msg": "🔴 Una idea que te ayudará es que, si llegas a presentar temblores en manos o boca y tienes dificultad para llevarte el vaso a la boca, utilices un popote flexible."}
    else:
        return "Las condiciones no cumplen con ninguna recomendación o alerta."


# ============================== TRAZOS ===========================

# IA
@app.route('/trazos/asignar', methods=['POST'])
def predecir_trazos():
    prom_res_eval  = request.json['prom_res_eval']
    idM= 0
    type = ""
    title = ""
    msg = ""

    if prom_res_eval <= 8:
        condiciones = "prom_res_eval <= 8"
        idM = 13
        type = "Recomendación"
        title = "🟢 Coordinación de manos"
        msg = "🟢 Te sugerimos seguir practicando ejercicios para mejorar la coordinación de tus manos, ya que tus trazos son claros y legibles."
    elif prom_res_eval >= 9 and prom_res_eval  <= 16:
        condiciones = "prom_res_eval >= 9 and prom_res_eval <= 16"
        idM = 14
        type = "Recomendación"
        title = "🟢 Postura al comer"
        msg = "🟢 Un punto a tener en cuenta es que cuando estés comiendo, te asegures de sentarte correctamente con la espalda recta y los pies apoyados en el suelo."
    elif prom_res_eval >= 17 and prom_res_eval <= 23:
        condiciones = "prom_res_eval >= 17 and prom_res_eval <= 23"
        type = "Recomendación"
        idM = 15
        title = "🟢 Ejercicio de tacto"
        msg = "🟢 Sigue haciendo ejercicios para mejorar la sensibilidad y el tacto en tus manos."
    elif prom_res_eval >= 24 and prom_res_eval <= 32:
        condiciones = "prom_res_eval >= 24 and prom_res_eval <= 32"
        type = "Recomendación"
        idM = 16
        title = "🟢 Estiramiento con banda de resistencia"
        msg = "🟢 Tu escritura se ve bien, ¡eso es genial!.Para mantener la fuerza y destreza en tus manos, te recomiendo seguir haciendo ejercicios de agarre y fuerza en tus dedos y manos."
    elif prom_res_eval >= 33 and prom_res_eval <= 39:
        condiciones = "prom_res_eval  >= 33 and prom_res_eval  <= 39"
        type = "Notificación"
        idM = 17
        title = "🟡 Motricidad fina con clips"
        msg = "🟡 Se detectó ligeros niveles de temblor en manos, se le propone aumentar los ejercicios de motricidad fina."
    elif prom_res_eval >= 40 and prom_res_eval <= 46:
        condiciones = "prom_res_eval >= 40 and prom_res_eval <= 46"
        type = "Notificación"
        idM = 18
        title = "🟡 Clasificación de objetos"
        msg = "🟡 Sus trazos presentan ligeras irregularidades, se recomienda aumentar los ejercicios de coordinación mano-ojo."
    elif prom_res_eval >= 47 and prom_res_eval <= 53:
        condiciones = "prom_res_eval >= 47 and prom_res_eval <= 53"
        type = "Notificación"
        idM = 19
        title = "🟡 Recorte con tijeras"
        msg = "🟡 Sus trazos tienen ligeras irregularidades, se le sugiere aumentar los ejercicios de habilidad manual."
    elif prom_res_eval >= 54 and prom_res_eval <= 60:
        condiciones = "prom_res_eval >= 54 and prom_res_eval <= 60"
        type = "Notificación"
        idM = 20
        title = "🟡 Ejercicio de escritura"
        msg = "🟡 Sus trazos tienen ligeras irregularidades, se recomienda aumentar su escritura a mano."
    elif prom_res_eval >= 61 and prom_res_eval <= 67:
        condiciones = "prom_res_eval >= 61 and prom_res_eval <= 67"
        type = "Notificación"
        idM = 21
        title = "🟡 Cubiertos adaptados"
        msg = "🟡 Un consejo práctico es que para comer puedes usar cubiertos ligeros y de tamaño adecuado para facilitar el manejo de los mismos."
    elif prom_res_eval >= 68 and prom_res_eval <= 74:
        condiciones = "prom_res_eval >= 68 and prom_res_eval <= 74"
        type = "Notificación"
        idM = 22
        title = "🟡 Tip para cepillarse los dientes"
        msg = "🟡 Si te cuesta cepillarte los dientes debido al temblor, una buena idea es utilizar un cepillo con el mango cubierto de goma espuma."
    elif prom_res_eval >= 75 and prom_res_eval <= 88:
        condiciones = "prom_res_eval >= 75 and prom_res_eval <= 88"
        type = "Alerta"
        idM = 23
        title = "🔴 Coordinación - Piernas y brazos"
        msg = "🔴 Te recomendamos seguir haciendo ejercicios que involucren coordinar tus piernas y brazos. Esto te ayudará a mejorar tu coordinación y mantener tu cuerpo en forma. ¡Sigue trabajando en ello!"
    elif prom_res_eval >= 89 and prom_res_eval <= 91:
        condiciones = "prom_res_eval >= 89 and prom_res_eval <= 91"
        type = "Alerta"
        idM = 24
        title = "🔴 Balancear el cuerpo"
        msg = "🔴 Si alguna vez te cuesta dar un paso y sientes sensaciones de parálisis, una buena idea es balancear tu cuerpo para ayudarte a dar el siguiente paso."
    elif prom_res_eval >= 92 and prom_res_eval <= 94:
        condiciones = "prom_res_eval >= 92 and prom_res_eval <= 94"
        type = "Alerta"
        idM = 25
        title = "🔴 Estímulos visuales"
        msg = "🔴 Mirar cosas a tu alrededor te ayudará si te quedas atrapado al moverte y tienes dificultades para seguir adelante. ¡Mantén tus ojos abiertos!"
    elif prom_res_eval >= 95 and prom_res_eval <= 97:
        condiciones = "prom_res_eval >= 95 and prom_res_eval <= 97"
        type = "Alerta"
        idM = 26
        title = "🔴 Estímulos auditivos"
        msg = "🔴 Escuchar sonidos a tu alrededor te ayudará si te quedas atrapado al moverte y tienes dificultades para seguir adelante.  ¡Presta atención a los sonidos que te rodean!"
    elif prom_res_eval >= 98 and prom_res_eval <= 100:
        condiciones = "prom_res_eval >= 98 and prom_res_eval <= 100"
        type = "Alerta"
        idM = 27
        title = "🔴 Cuenta mental"
        msg = "🔴 Contar tus pasos en voz alta y a un ritmo constante te ayudará si te quedas atrapado al moverte y tienes dificultades para avanzar."
    else:
        return "Las condiciones no cumplen con ninguna recomendación, notificación o alerta."


    respuesta = {
        "condiciones": condiciones,
        "registro": {
            "prom_res_eval ": prom_res_eval 
        },
        "result": {
            "id": idM,
            "type": type,
            "title": title,
            "msg": msg
        }
    }

    enviar_notificacion(type, title, msg)
    insertar_registro(idM, 3, 2)

    return jsonify(respuesta)




# +++++++++++++++++++++++++++++++++ ENVIO DE NOTIFICACION PUSH
def enviar_notificacion(type, title, msg):

    imgType = ''
    # Validar el tipo de mensaje
    if type == "Recomendación":
        imgType = 'https://cdn-icons-png.flaticon.com/512/9482/9482226.png'
    elif type == "Notificación":
        imgType = 'https://cdn-icons-png.flaticon.com/512/3602/3602137.png'
    elif type == "Alerta":
        imgType = 'https://cdn-icons-png.flaticon.com/512/5974/5974693.png'
    elif type == "Mensaje":
        imgType = 'https://cdn-icons-png.flaticon.com/512/893/893257.png'
    else:
        imgType = 'https://cdn-icons-png.flaticon.com/512/893/893257.png'



    # Definir la URL del EndPoint
    url = "https://fcm.googleapis.com/fcm/send"

    # Definir los encabezados
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer AAAA30T5osU:APA91bHK1OsjE_XzQ62cA6xz4sQderER5ruQD-43xZ44qvaIaYmnkkzBCP-rsImq6LoZsohAuaFvkxTY-R9L7gXx2x5kXLYekLg2YXnvgxEMAW0dj6xWrMVBYeSnrHe9MbBNzTKAx7BW"
    }

    # Definir el cuerpo de la solicitud
    data = {
        "notification": {
            "title": title,
            "body": msg,
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "image": imgType,
            "color": "#E92D3B",
            "tag": type
        },
        "to": "eIewiodmSemsYWbHLmHLhI:APA91bE9h9HJU2cuTYg6FoYsamlVTa1qlahAOE_cAwgQI52spaldC-ggs364dn9VKpPO0nYpR5rGp_HINuu8tvXEMrxJicYMKyeTx4Q2MPp200kKG_yNNkv3KtpUhhU49M0UIvGUHGvV"
    }

    # Convertir el cuerpo de la solicitud a JSON
    json_data = json.dumps(data)

    # Enviar la solicitud POST
    response = requests.post(url, headers=headers, data=json_data)

    # Verificar el estado de la respuesta
    if response.status_code == 200:
        print("La solicitud PUSH se ha enviado correctamente.")
    else:
        print("Error al enviar la solicitud. Código de estado:", response.status_code)




# +++++++++++++++++++++++++++++++++ ENVIO DE NOTIFICACION WhatsApp - Twilio

def enviar_whatsapp():
    account_sid = 'AC05b51705975fc5d992a9a3317dba2dc3'
    auth_token = 'cae4532449e6869826bd27faea76f090'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_='whatsapp:+5213341702159',
        body='Gracias por usar los servicios de PreventSoft.',
        to='whatsapp:+522711942415'
    )

    print(f"Mensaje enviado. SID del mensaje: {message.sid}")


# =========================insertar el registro =================

def insertar_registro(idMensaje, idPaciente, idMedico):
    idPacienteX = 6
    idMedicoX = 2
    try:
        # Conexión a la base de datos
        connection = mysql.connector.connect(
            host='preventsoft.com ',
            port=3306,
            user='jalorhco_antonio',
            password='minayork1985!',
            database='jalorhco_modulo'
        )

        # Crear el cursor
        cursor = connection.cursor()

        # Obtener la fecha actual del sistema
        fecha = datetime.now()

        # Insertar el registro en la tabla
        query = "INSERT INTO `BUZON.PROC.MENSAJES` (fecha, idMensaje, idPaciente, idMedico, estado) VALUES (%s, %s, %s, %s, %s)"
        values = (fecha, idMensaje, idPacienteX, idMedicoX, 1)  # estado por defecto en 1

        cursor.execute(query, values)

        # Confirmar los cambios en la base de datos
        connection.commit()

        print("REGISTRO insertado correctamente")

    except Error as e:
        print("Error al insertar el registro:", e)

    finally:
        # Cerrar el cursor y la conexión a la base de datos
        if connection.is_connected():
            cursor.close()
            connection.close()







# ============================================================
# ======================================== RUN ===============
if __name__ == '__main__':
    app.run(debug=True, port=port)

