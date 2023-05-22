# Blackchain

# Descripción

Blackchain es una blockchain basada en python y SHA256, como toda blockchain, se minan bloques y se pueden realizar transacciones entre los usuarios usando Pinkcoins ($PNK).

# ¿Cómo está construida?

La blockchain como tal es una clase, la cual tiene la cadena, transacciones (mempool), cuentas (llaves privadas y balance), bloques y nodos. Cuando se van minando los bloques, se van agregando las transacciones, actualizando balances y añadiendo los propios bloques a la cadena.

# Uso y explicación

## 1. Instalación y ejecución.
   
`git clone https://github.com/vapemx/Blackchain`

`pip install flask`

Cada terminal en donde se esté ejecutando la blockchain será un nodo de la red, para esto, se le debe pasar el parámetro donde estará corriendo cada nodo (a partir del puerto 5000).

`py blackchain.py -p 5001`

Para el siguiente nodo:

`py blackchain.py -p 5002`

... y así sucesivamente.
   
A partir de ahora estaremos utilizando Postman para el envío de peticiones y ejecución de la blockchain en la dirección http://127.0.0.1:{puerto}/. 

Por ejemplo: `http://127.0.0.1:5001/`

## 2. Conexión entre nodos.
   
Supongamos que estamos trabajando con 3 nodos.

- http://127.0.0.1:5001/
- http://127.0.0.1:5002/
- http://127.0.0.1:5003/

Para cada nodo, estaremos haciendo una petición POST en Postman http://127.0.0.1:5001/connect_node, y enviaremos en JSON una lista de los nodos a conectar, en este caso, haciendo la petición del 5001, nos conectamos al 5002 y 5003 de la siguiente manera:

``
{
"nodes":["http://127.0.0.1:5002", "http://127.0.0.1:5003"]
}
``

Para el 5002, sólo enviaremos la dirección del 5001 y 5003. Para el 5003, enviamos la dirección del 5001 y 5002.

## 3. Crear una wallet para cada nodo.

Utilizando el método POST en http://127.0.0.1:5001/create_wallet, añadimos el envío de un JSON con el siguiente formato:

```
{
    "entropy": ""
}
```

donde el valor de entropía será cualquier string dada por el usuario. Esto será para generar llaves aleatorias.

El algoritmo de generación de llaves es el siguiente:

- Se suma el valor ASCII de cada caracter de la entropía, a lo que llamaremos 'seed'.
- La llave privada es el hash de la seed multiplicado por un número aleatorio entre 1 y seed^2.
- La llave pública es el hash de la llave privada.

Al usuario se le entregan ambas llaves tanto en pantalla como en un archivo para cada llave.

Es importante crear una wallet para cada nodo.

## 4. Operación
Una vez conectados todos los nodos, todos tendrán el bloque génesis, a partir de ahora ya se podrá operar libremente con las siguientes peticiones:

Por ejemplo: `http://127.0.0.1:5001/get_chain`

### /get_chain:
[GET] Muestra toda la cadena cargada en el nodo.
    
### /is_valid:
[GET] Comprueba la validez de la cadena a través de sus hashes.

### /get_chain:
[GET] Comprueba si nuestro nodo contiene la cadena más larga, en caso de no ser así, la cadena más larga se toma como válida y ahora es la que estará cargada en nuestro nodo.

### /add_transaction:
[POST] Se envía un JSON de la siguiente manera:

``
{
    "sender": "",
    "receiver": "",
    "amount": 10
}
``

Como en la vida real, nosotros solo podemos enviar dinero de nuestra cuenta a alguien más. No podemos quitarle el dinero a un desconocido para pagar nuestras deudas.

Para esto, el valor de "sender" debe ser nuestra llave privada, es con la que nosotros vamos a aprobar la transacción, ya que nadie más tiene este llave.

Por el algoritmo de encriptadode la blockchain, se extrae la llave pública de esta cuenta, la cual sí está contenida en la blockchain junto con el balance disponible.

El receiver es la llave pública que recibirá los $PNK. Y el amount la cantidad de estos.

Una vez pasadas algunas comprobaciones de balances y cuentas, la transacción será agregada al mempool, esperando al siguiente bloque minado para ejecutar la transacción.

### /mine_block:
[GET] Se envía junto con un JSON, para que, en caso de ser el minador ganador, se entrega la recompensa de 1 $PNK.

``
{
    "receiver": ""
}
``

Teniendo en cuenta el hash y proof del anterior bloque, se ejecuta la prueba de trabajo que consiste en que los primeros 4 caracteres del hash sean 0 ('0000'), mientras que la manera de obtener el hash es el proof(iteración)^2 - el proof del anterior bloque^2.

En caso de que el nodo que hizo la petición resulte ganador, se añade la transacción de recompensa al mempool y se crea el nuevo bloque.

## 5. Escenario real

Una vez que los nodos estén conectados entre sí y con una wallet creada, ya cada uno estará intentando minar los bloques y creando transacciones.

Al estar minando, siempre va a pasar que va a haber una cadena más larga que la de los otros nodos, para esto, se comprueba la cadena con /get_chain y en caso de que haya una cadena más larga, se utiliza /replace_chain en los nodos para que estos contengan la cadena más larga (la válida).

No es necesario que todos los nodos tengan la intención de minar bloques, ya que puede haber un nodo que sólo quiera transaccionar con $PNK, lo cual es completamente valido y posible, sin embargo, al igual que todos los nodos, se tendrá que estar validando y actualizando la cadena más larga.