from PIL import Image
from pathlib import Path


def extraer_sprites(ruta_imagen, filas, columnas, carpeta_salida):
    """
    Recorta una hoja de sprites en imágenes individuales.
    """
    ruta_script = Path(__file__).parent
    ruta_imagen = ruta_script / ruta_imagen
    carpeta_salida = ruta_script / carpeta_salida

    carpeta_salida.mkdir(parents=True, exist_ok=True)

    try:
        hoja_sprites = Image.open(ruta_imagen)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ruta_imagen}")
        return

    ancho_total, alto_total = hoja_sprites.size

    ancho_sprite = ancho_total // columnas
    alto_sprite = alto_total // filas

    contador = 1

    print(f"Resolución total: {ancho_total}x{alto_total}")
    print(f"Tamaño estimado por sprite: {ancho_sprite}x{alto_sprite}")

    for fila in range(filas):
        for col in range(columnas):
            izquierda = col * ancho_sprite
            superior = fila * alto_sprite
            derecha = izquierda + ancho_sprite
            inferior = superior + alto_sprite

            caja = (izquierda, superior, derecha, inferior)
            sprite = hoja_sprites.crop(caja)

            nombre_archivo = f"sprite_{contador:02d}.png"
            ruta_guardado = carpeta_salida / nombre_archivo

            sprite.save(ruta_guardado)
            print(f"Guardado: {ruta_guardado}")

            contador += 1

    hoja_sprites.close()
    print(f"\nProceso terminado. Se extrajeron {contador - 1} sprites.")


# --- Configuración ---
archivo_imagen = "sprites.jpg"

filas_en_imagen = 5
columnas_en_imagen = 4

carpeta_destino = "sprites_extraidos"

extraer_sprites(
    archivo_imagen,
    filas_en_imagen,
    columnas_en_imagen,
    carpeta_destino
)