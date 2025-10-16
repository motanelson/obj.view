"""
Simple .obj viewer
- Fundo amarelo
- Objeto amarelo escuro
- Abridor de ficheiros (pressione O ou carregue um ficheiro ao arrancar)

Dependências: pip install pygame PyOpenGL numpy
Execute: python viewer_obj.py
"""

import sys
import math
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import tkinter as tk
from tkinter import filedialog


def load_obj(path):
    """Carrega vértices e faces simples de um ficheiro .obj (triângulos ou polígonos).
    Retorna (vertices, faces)
    faces: lista de listas de índices (0-based)
    """
    verts = []
    faces = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'v':
                    x, y, z = map(float, parts[1:4])
                    verts.append((x, y, z))
                elif parts[0] == 'f':
                    face = []
                    for v in parts[1:]:
                        # formatos: v, v/vt, v//vn, v/vt/vn
                        idx = v.split('/')[0]
                        if idx:
                            face.append(int(idx) - 1)
                    if len(face) >= 3:
                        # triangular faces com fan
                        if len(face) == 3:
                            faces.append(face)
                        else:
                            # converter polígonos para triângulos (fan)
                            for i in range(1, len(face)-1):
                                faces.append([face[0], face[i], face[i+1]])
    except Exception as e:
        print('Erro ao carregar OBJ:', e)
    return verts, faces


def compute_normal(v0, v1, v2):
    a = np.array(v1) - np.array(v0)
    b = np.array(v2) - np.array(v0)
    n = np.cross(a, b)
    norm = np.linalg.norm(n)
    if norm == 0:
        return (0.0, 0.0, 1.0)
    return tuple(n / norm)


def draw_mesh(verts, faces):
    glBegin(GL_TRIANGLES)
    for f in faces:
        v0 = verts[f[0]]
        v1 = verts[f[1]]
        v2 = verts[f[2]]
        nx, ny, nz = compute_normal(v0, v1, v2)
        glNormal3f(nx, ny, nz)
        for idx in f:
            glVertex3f(*verts[idx])
    glEnd()


def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    filetypes = [('Wavefront OBJ', '*.obj'), ('All files', '*.*')]
    path = filedialog.askopenfilename(title='Abrir ficheiro .obj', filetypes=filetypes)
    root.destroy()
    return path


def main():
    # Abrir ficheiro inicialmente
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = open_file_dialog()
    if not path:
        print('Nenhum ficheiro selecionado. A sair.')
        return

    verts, faces = load_obj(path)
    if not verts or not faces:
        print('Ficheiro vazio ou sem faces válidas.')
        return

    # DEBUG: Mostrar estatísticas dos vértices
    vs = np.array(verts)
    print(f"Vértices carregados: {len(verts)}")
    print(f"Faces carregadas: {len(faces)}")
    print(f"Range X: {vs[:,0].min():.2f} to {vs[:,0].max():.2f}")
    print(f"Range Y: {vs[:,1].min():.2f} to {vs[:,1].max():.2f}") 
    print(f"Range Z: {vs[:,2].min():.2f} to {vs[:,2].max():.2f}")
    print(f"Centro: {vs.mean(axis=0)}")

    pygame.init()
    screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    pygame.display.set_caption('OBJ Viewer')

    # Configurações do OpenGL
    glClearColor(1.0, 1.0, 0.4, 1.0)  # Fundo AMARELO
    glEnable(GL_DEPTH_TEST)
    
    # Lighting
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (2, 2, 2, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
    
    # Material amarelo escuro (usando glColorMaterial - abordagem simples)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Projeção
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (800/600), 0.1, 100.0)
    
    # Configurações iniciais
    zoom = 5.0
    rot_x = 0.0
    rot_y = 0.0

    mouse_down = False
    last_mouse = (0, 0)

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_o:
                    newpath = open_file_dialog()
                    if newpath:
                        verts, faces = load_obj(newpath)
                elif event.key == K_r:
                    rot_x = rot_y = 0.0
                elif event.key == K_UP:
                    zoom -= 1.0
                elif event.key == K_DOWN:
                    zoom += 1.0
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
                    last_mouse = event.pos
                elif event.button == 4:
                    zoom -= 0.5
                elif event.button == 5:
                    zoom += 0.5
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            elif event.type == MOUSEMOTION:
                if mouse_down:
                    dx = event.pos[0] - last_mouse[0]
                    dy = event.pos[1] - last_mouse[1]
                    rot_x += dy * 0.5
                    rot_y += dx * 0.5
                    last_mouse = event.pos

        # Limpar ecrã
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Configurar vista da câmera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, zoom, 0, 0, 0, 0, 1, 0)

        # Aplicar rotações
        glRotatef(rot_x, 1, 0, 0)
        glRotatef(rot_y, 0, 1, 0)

        # Desenhar objeto carregado
        if verts and faces:
            glColor3f(0.6, 0.5, 0.0)  # Amarelo escuro
            draw_mesh(verts, faces)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()
