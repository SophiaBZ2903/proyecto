"""
REFLEJO - Prototipo con sistema de tiles + sprites
Carga imágenes desde assets/sprites/ y usa placeholders si no existen.

Estructura esperada:
    reflejo_sprites.py
    nivel1.txt
    assets/
        sprites/
            lumen.png
            umbra.png
            pared.png
            suelo.png
            meta_lumen.png
            meta_umbra.png

Si falta algún archivo, se genera un placeholder automáticamente.

Controles:
- Flechas o WASD: mover
- R: reiniciar
- ESC: salir
"""

import pygame
import sys
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================
TAM_TILE = 40
COLUMNAS = 20
FILAS = 15
ANCHO = TAM_TILE * COLUMNAS
ALTO = TAM_TILE * FILAS
FPS = 60
VELOCIDAD = 5

# Colores (para placeholders y UI)
NEGRO = (20, 20, 30)
BLANCO = (240, 240, 240)
AZUL_LUMEN = (100, 180, 255)
ROJO_UMBRA = (220, 80, 80)
GRIS_PARED = (60, 60, 80)
GRIS_SUELO = (35, 35, 50)
VERDE_META = (100, 220, 130)

# Rutas
DIR_BASE = os.path.dirname(__file__)
DIR_SPRITES = os.path.join(DIR_BASE, "assets", "sprites")


# ============================================================
# CARGA DE SPRITES
# ============================================================
def crear_placeholder(color, tipo="solido"):
    """
    Genera un Surface de TAM_TILE con un patrón básico.
    Útil mientras no tienes los sprites reales.
    """
    surf = pygame.Surface((TAM_TILE, TAM_TILE), pygame.SRCALPHA)
    surf.fill(color)

    if tipo == "pared":
        # Bordes oscuros para simular ladrillos
        pygame.draw.rect(surf, NEGRO, surf.get_rect(), 2)
        pygame.draw.line(surf, (40, 40, 60), (0, TAM_TILE // 2),
                         (TAM_TILE, TAM_TILE // 2), 1)
    elif tipo == "suelo":
        # Punteado sutil
        for i in range(0, TAM_TILE, 8):
            for j in range(0, TAM_TILE, 8):
                pygame.draw.circle(surf, (45, 45, 65), (i, j), 1)
    elif tipo == "meta":
        # Marco brillante
        pygame.draw.rect(surf, BLANCO, surf.get_rect(), 2)
        pygame.draw.circle(surf, BLANCO, (TAM_TILE // 2, TAM_TILE // 2),
                           TAM_TILE // 4, 2)
    elif tipo == "jugador":
        # Círculo con borde para que se vea como personaje
        pygame.draw.circle(surf, color,
                           (TAM_TILE // 2, TAM_TILE // 2), TAM_TILE // 2 - 4)
        pygame.draw.circle(surf, BLANCO,
                           (TAM_TILE // 2, TAM_TILE // 2), TAM_TILE // 2 - 4, 2)

    return surf


def cargar_sprite(nombre_archivo, color_placeholder, tipo_placeholder):
    """
    Intenta cargar una imagen. Si no existe, devuelve un placeholder.
    Esto permite trabajar sin tener los sprites finales todavía.
    """
    ruta = os.path.join(DIR_SPRITES, nombre_archivo)
    if os.path.exists(ruta):
        # convert_alpha() optimiza la imagen para el formato de pantalla
        # y respeta la transparencia. Es importante para el rendimiento.
        imagen = pygame.image.load(ruta).convert_alpha()
        # Escalamos al tamaño del tile por si el sprite original es más grande
        return pygame.transform.scale(imagen, (TAM_TILE, TAM_TILE))
    else:
        print(f"[INFO] Sprite no encontrado: {nombre_archivo}. Usando placeholder.")
        return crear_placeholder(color_placeholder, tipo_placeholder)


# ============================================================
# CLASE NIVEL
# ============================================================
class Nivel:
    def __init__(self, ruta_archivo, sprites):
        self.paredes = []
        self.tiles_decorativos = []  # Lista de (sprite, rect) para dibujar
        self.meta_lumen = None
        self.meta_umbra = None
        self.spawn_lumen = (0, 0)
        self.spawn_umbra = (0, 0)
        self.sprites = sprites
        self.cargar(ruta_archivo)

    def cargar(self, ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = f.read().splitlines()

        for fila, linea in enumerate(lineas):
            for col, caracter in enumerate(linea):
                x = col * TAM_TILE
                y = fila * TAM_TILE
                rect = pygame.Rect(x, y, TAM_TILE, TAM_TILE)

                if caracter == "#":
                    self.paredes.append(rect)
                    self.tiles_decorativos.append((self.sprites["pared"], rect))
                elif caracter == "L":
                    self.spawn_lumen = (x, y)
                elif caracter == "U":
                    self.spawn_umbra = (x, y)
                elif caracter == "1":
                    self.meta_lumen = rect
                elif caracter == "2":
                    self.meta_umbra = rect

    def dibujar(self, pantalla):
        # 1. Suelo de fondo: dibujamos un patrón cubriendo toda la pantalla
        # Esto da textura al fondo. Lo hacemos con tiles repetidos.
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                pantalla.blit(self.sprites["suelo"],
                              (col * TAM_TILE, fila * TAM_TILE))

        # 2. Paredes (encima del suelo)
        for sprite, rect in self.tiles_decorativos:
            pantalla.blit(sprite, rect)

        # 3. Metas (encima del suelo, identificables por color)
        if self.meta_lumen:
            pantalla.blit(self.sprites["meta_lumen"], self.meta_lumen)
        if self.meta_umbra:
            pantalla.blit(self.sprites["meta_umbra"], self.meta_umbra)


# ============================================================
# CLASE JUGADOR
# ============================================================
class Jugador:
    def __init__(self, x, y, sprite, espejo_x=False):
        margen = 4
        self.rect = pygame.Rect(
            x + margen, y + margen,
            TAM_TILE - margen * 2, TAM_TILE - margen * 2
        )
        self.sprite = sprite
        self.espejo_x = espejo_x

    def mover(self, dx, dy, paredes):
        if self.espejo_x:
            dx = -dx

        self.rect.x += dx
        for pared in paredes:
            if self.rect.colliderect(pared):
                if dx > 0:
                    self.rect.right = pared.left
                elif dx < 0:
                    self.rect.left = pared.right

        self.rect.y += dy
        for pared in paredes:
            if self.rect.colliderect(pared):
                if dy > 0:
                    self.rect.bottom = pared.top
                elif dy < 0:
                    self.rect.top = pared.bottom

    def dibujar(self, pantalla):
        # Centramos el sprite sobre el rect del jugador
        # (el rect es un poco más pequeño que el tile por el margen)
        pantalla.blit(self.sprite,
                      (self.rect.x - 4, self.rect.y - 4))


# ============================================================
# UTILIDADES
# ============================================================
def comprobar_victoria(lumen, umbra, nivel):
    en_meta_l = nivel.meta_lumen and lumen.rect.colliderect(nivel.meta_lumen)
    en_meta_u = nivel.meta_umbra and umbra.rect.colliderect(nivel.meta_umbra)
    return en_meta_l and en_meta_u


# ============================================================
# INICIALIZACIÓN
# ============================================================
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Reflejo - Sistema de Sprites")
reloj = pygame.time.Clock()
fuente = pygame.font.SysFont("Arial", 22, bold=True)
fuente_grande = pygame.font.SysFont("Arial", 48, bold=True)


# ============================================================
# CARGAR TODOS LOS SPRITES (una sola vez al inicio)
# ============================================================
# Diccionario centralizado: la clave es el "tipo de tile",
# el valor es la imagen lista para dibujar.
sprites = {
    "pared": cargar_sprite("pared.png", GRIS_PARED, "pared"),
    "suelo": cargar_sprite("suelo.png", GRIS_SUELO, "suelo"),
    "meta_lumen": cargar_sprite("meta_lumen.png", AZUL_LUMEN, "meta"),
    "meta_umbra": cargar_sprite("meta_umbra.png", ROJO_UMBRA, "meta"),
    "lumen": cargar_sprite("lumen.png", AZUL_LUMEN, "jugador"),
    "umbra": cargar_sprite("umbra.png", ROJO_UMBRA, "jugador"),
}


# ============================================================
# CARGAR NIVEL
# ============================================================
def iniciar_nivel(ruta):
    nivel = Nivel(ruta, sprites)
    lumen = Jugador(*nivel.spawn_lumen, sprites["lumen"], espejo_x=False)
    umbra = Jugador(*nivel.spawn_umbra, sprites["umbra"], espejo_x=True)
    return nivel, lumen, umbra


ruta_nivel = os.path.join(DIR_BASE, "nivel1.txt")
nivel, lumen, umbra = iniciar_nivel(ruta_nivel)
victoria = False


# ============================================================
# GAME LOOP
# ============================================================
ejecutando = True
while ejecutando:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.key == pygame.K_r:
                nivel, lumen, umbra = iniciar_nivel(ruta_nivel)
                victoria = False

    if not victoria:
        teclas = pygame.key.get_pressed()
        dx, dy = 0, 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx = -VELOCIDAD
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx = VELOCIDAD
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy = -VELOCIDAD
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy = VELOCIDAD

        lumen.mover(dx, dy, nivel.paredes)
        umbra.mover(dx, dy, nivel.paredes)

        if comprobar_victoria(lumen, umbra, nivel):
            victoria = True

    # --- RENDERIZADO ---
    nivel.dibujar(pantalla)
    lumen.dibujar(pantalla)
    umbra.dibujar(pantalla)

    texto = fuente.render("WASD/Flechas: mover  |  R: reiniciar  |  ESC: salir",
                          True, BLANCO)
    # Sombra para que el texto se lea sobre cualquier fondo
    sombra = fuente.render("WASD/Flechas: mover  |  R: reiniciar  |  ESC: salir",
                           True, NEGRO)
    pantalla.blit(sombra, (12, 7))
    pantalla.blit(texto, (10, 5))

    if victoria:
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(180)
        overlay.fill(NEGRO)
        pantalla.blit(overlay, (0, 0))

        texto_victoria = fuente_grande.render("¡NIVEL COMPLETADO!", True, VERDE_META)
        rect_texto = texto_victoria.get_rect(center=(ANCHO // 2, ALTO // 2 - 20))
        pantalla.blit(texto_victoria, rect_texto)

        texto_reinicio = fuente.render("Presiona R para reiniciar", True, BLANCO)
        rect_reinicio = texto_reinicio.get_rect(center=(ANCHO // 2, ALTO // 2 + 30))
        pantalla.blit(texto_reinicio, rect_reinicio)

    pygame.display.flip()
    reloj.tick(FPS)


pygame.quit()
sys.exit()