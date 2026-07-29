"""
gl_viewport.py
--------------
OpenGL 3D Viewport Widget and mesh/texture handling.
"""

from __future__ import annotations
import math
import ctypes
import numpy as np
import os

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QSurfaceFormat

import OpenGL.GL as gl
from OpenGL.GL import shaders

VERT_SRC = """
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec3 in_tangent;
layout(location = 3) in vec2 in_uv;

uniform mat4  u_model;
uniform mat4  u_view;
uniform mat4  u_proj;
uniform mat3  u_normal_mat;

out vec3 v_frag_pos;
out vec2 v_uv;
out mat3 v_tbn;

void main() {
    vec4 world_pos = u_model * vec4(in_position, 1.0);
    v_frag_pos     = world_pos.xyz;
    v_uv           = in_uv;

    vec3 N = normalize(u_normal_mat * in_normal);
    vec3 T = normalize(u_normal_mat * in_tangent);
    T      = normalize(T - dot(T, N) * N);
    vec3 B = cross(N, T);
    v_tbn  = mat3(T, B, N);

    gl_Position = u_proj * u_view * world_pos;
}
"""

FRAG_SRC = """
#version 330 core
in vec3 v_frag_pos;
in vec2 v_uv;
in mat3 v_tbn;

uniform sampler2D u_albedo;
uniform sampler2D u_normal_map;
uniform sampler2D u_heightmap;
uniform sampler2D u_ao_map;
uniform sampler2D u_roughness_map;
uniform sampler2D u_metal_map;

uniform vec3  u_light_dir;  
uniform vec3  u_light_color;
uniform vec3  u_fill_dir;   
uniform vec3  u_fill_color;
uniform vec3  u_rim_dir;    
uniform vec3  u_rim_color;

uniform vec3  u_cam_pos;
uniform float u_bump_scale;
uniform float u_ao_strength;

uniform int   u_has_albedo;
uniform int   u_has_normal;
uniform int   u_has_height;
uniform int   u_has_ao;
uniform int   u_has_roughness;
uniform int   u_has_metal;

out vec4 frag_color;

void main() {
    vec3 base_color = (u_has_albedo == 1) ? texture(u_albedo, v_uv).rgb : vec3(0.72, 0.72, 0.75);

    vec3 N;
    if (u_has_normal == 1) {
        vec3 nm = texture(u_normal_map, v_uv).rgb * 2.0 - 1.0;
        N = normalize(v_tbn * nm);
    } else {
        N = normalize(v_tbn[2]);
    }

    if (u_has_height == 1) {
        float bump = texture(u_heightmap, v_uv).r * u_bump_scale;
        N = normalize(N + v_tbn[2] * bump);
    }

    float ao = (u_has_ao == 1) ? mix(1.0, texture(u_ao_map, v_uv).r, u_ao_strength) : 1.0;
    float rough_val = (u_has_roughness == 1) ? texture(u_roughness_map, v_uv).r : 0.5;
    float metal_val = (u_has_metal == 1) ? texture(u_metal_map, v_uv).r : 0.0;

    vec3 diffuse_color = base_color * (1.0 - metal_val);
    vec3 F0 = mix(vec3(0.04), base_color, metal_val);

    float shininess = mix(256.0, 4.0, rough_val);
    float spec_strength = mix(1.0, 0.1, rough_val);

    vec3 V = normalize(u_cam_pos - v_frag_pos);
    vec3 L = normalize(-u_light_dir);
    vec3 H = normalize(L + V);

    float diff_key = max(dot(N, L), 0.0);
    float spec_key = pow(max(dot(N, H), 0.0), shininess) * spec_strength;

    vec3 L_fill = normalize(-u_fill_dir);
    float diff_fill = max(dot(N, L_fill), 0.0);

    vec3 L_rim = normalize(-u_rim_dir);
    vec3 H_rim = normalize(L_rim + V);
    float rim_fresnel = smoothstep(0.5, 1.0, 1.0 - max(dot(V, N), 0.0));
    float diff_rim = max(dot(N, L_rim), 0.0) * rim_fresnel;
    float spec_rim = pow(max(dot(N, H_rim), 0.0), shininess * 0.5) * spec_strength * rim_fresnel;

    vec3 ambient = 0.15 * base_color * ao;
    vec3 diffuse = ((diff_key * u_light_color) + (diff_fill * u_fill_color) + (diff_rim * u_rim_color)) * diffuse_color * ao;
    vec3 specular = (spec_key * u_light_color * F0 * 2.0) + (spec_rim * u_rim_color * F0 * 2.0);

    float exposure = 1.3; 
    frag_color = vec4((ambient + diffuse + specular) * exposure, 1.0);
}
"""


def _build_cube() -> tuple[np.ndarray, np.ndarray]:
    faces = [
        [(-1, -1,  1), (0, 0, 1), (1, 0, 0), (0, 0)],
        [( 1, -1,  1), (0, 0, 1), (1, 0, 0), (1, 0)],
        [( 1,  1,  1), (0, 0, 1), (1, 0, 0), (1, 1)],
        [(-1,  1,  1), (0, 0, 1), (1, 0, 0), (0, 1)],
        [( 1, -1, -1), (0, 0, -1), (-1, 0, 0), (0, 0)],
        [(-1, -1, -1), (0, 0, -1), (-1, 0, 0), (1, 0)],
        [(-1,  1, -1), (0, 0, -1), (-1, 0, 0), (1, 1)],
        [( 1,  1, -1), (0, 0, -1), (-1, 0, 0), (0, 1)],
        [( 1, -1,  1), (1, 0, 0), (0, 0, -1), (0, 0)],
        [( 1, -1, -1), (1, 0, 0), (0, 0, -1), (1, 0)],
        [( 1,  1, -1), (1, 0, 0), (0, 0, -1), (1, 1)],
        [( 1,  1,  1), (1, 0, 0), (0, 0, -1), (0, 1)],
        [(-1, -1, -1), (-1, 0, 0), (0, 0, 1), (0, 0)],
        [(-1, -1,  1), (-1, 0, 0), (0, 0, 1), (1, 0)],
        [(-1,  1,  1), (-1, 0, 0), (0, 0, 1), (1, 1)],
        [(-1,  1, -1), (-1, 0, 0), (0, 0, 1), (0, 1)],
        [(-1,  1,  1), (0, 1, 0), (1, 0, 0), (0, 0)],
        [( 1,  1,  1), (0, 1, 0), (1, 0, 0), (1, 0)],
        [( 1,  1, -1), (0, 1, 0), (1, 0, 0), (1, 1)],
        [(-1,  1, -1), (0, 1, 0), (1, 0, 0), (0, 1)],
        [(-1, -1, -1), (0, -1, 0), (1, 0, 0), (0, 0)],
        [( 1, -1, -1), (0, -1, 0), (1, 0, 0), (1, 0)],
        [( 1, -1,  1), (0, -1, 0), (1, 0, 0), (1, 1)],
        [(-1, -1,  1), (0, -1, 0), (1, 0, 0), (0, 1)],
    ]
    verts = []
    for f in faces:
        verts.extend([*f[0], *f[1], *f[2], *f[3]])
    indices = []
    for i in range(0, len(faces), 4):
        indices += [i, i + 1, i + 2, i, i + 2, i + 3]
    return np.array(verts, dtype=np.float32), np.array(indices, dtype=np.uint32)


def _build_sphere(stacks: int = 32, slices: int = 32) -> tuple[np.ndarray, np.ndarray]:
    verts = []
    for i in range(stacks + 1):
        phi = math.pi * i / stacks
        for j in range(slices + 1):
            theta = 2 * math.pi * (1.0 - j / slices)
            x = math.sin(phi) * math.cos(theta)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(theta)
            verts.extend([
                x, y, z,
                x, y, z,
                math.sin(theta), 0.0, -math.cos(theta),
                j / slices, 1.0 - (i / stacks)
            ])
    indices = []
    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = (i + 1) * (slices + 1) + j
            indices += [a, b, a + 1, b, b + 1, a + 1]
    return np.array(verts, dtype=np.float32), np.array(indices, dtype=np.uint32)


def _parse_idx(idx_str: str, max_count: int) -> int:
    if not idx_str:
        return -1
    try:
        val = int(idx_str)
        if val > 0:
            return val - 1
        elif val < 0:
            return max_count + val
        else:
            return -1
    except ValueError:
        return -1


def _load_obj(filepath: str) -> tuple[np.ndarray, np.ndarray]:
    v, vt, vn = [], [], []
    faces = []

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if not line:
                continue
            parts = line.split()
            tag = parts[0].lower()

            if tag == 'v' and len(parts) >= 4:
                v.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif tag == 'vt' and len(parts) >= 3:
                vt.append([float(parts[1]), float(parts[2])])
            elif tag == 'vn' and len(parts) >= 4:
                vn.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif tag == 'f' and len(parts) >= 4:
                raw_verts = parts[1:]
                for k in range(1, len(raw_verts) - 1):
                    faces.append((raw_verts[0], raw_verts[k], raw_verts[k + 1]))

    if not v or not faces:
        return _build_cube()

    v_arr = np.array(v, dtype=np.float32)
    min_v, max_v = np.min(v_arr, axis=0), np.max(v_arr, axis=0)
    center = (max_v + min_v) / 2.0
    extent = np.max(max_v - min_v)
    scale = 2.0 / (extent + 1e-8)
    v_arr = (v_arr - center) * scale

    verts = []
    indices = []
    idx_map = {}

    for tri in faces:
        tri_indices = []
        for v_str in tri:
            vals = v_str.split('/')
            vi = _parse_idx(vals[0], len(v))
            vti = _parse_idx(vals[1], len(vt)) if len(vals) > 1 else -1
            vni = _parse_idx(vals[2], len(vn)) if len(vals) > 2 else -1
            tri_indices.append((vi, vti, vni, v_str))

        if any(vi < 0 or vi >= len(v_arr) for vi, _, _, _ in tri_indices):
            continue

        p0, p1, p2 = v_arr[tri_indices[0][0]], v_arr[tri_indices[1][0]], v_arr[tri_indices[2][0]]

        fn = np.cross(p1 - p0, p2 - p0)
        fn_len = np.linalg.norm(fn)
        fn = fn / fn_len if fn_len > 1e-8 else np.array([0.0, 1.0, 0.0], dtype=np.float32)

        has_uvs = (len(vt) > 0 and all(0 <= vti < len(vt) for _, vti, _, _ in tri_indices))
        if has_uvs:
            uv0 = np.array(vt[tri_indices[0][1]], dtype=np.float32)
            uv1 = np.array(vt[tri_indices[1][1]], dtype=np.float32)
            uv2 = np.array(vt[tri_indices[2][1]], dtype=np.float32)
            du1, du2 = uv1 - uv0, uv2 - uv0
            dp1, dp2 = p1 - p0, p2 - p0
            det = du1[0] * du2[1] - du1[1] * du2[0]
            if abs(det) > 1e-8:
                tangent = (dp1 * du2[1] - dp2 * du1[1]) / det
                t_len = np.linalg.norm(tangent)
                tangent = tangent / t_len if t_len > 1e-8 else np.array([1.0, 0.0, 0.0], dtype=np.float32)
            else:
                tangent = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        else:
            tangent = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        for vi, vti, vni, key in tri_indices:
            if key not in idx_map:
                pos = v_arr[vi]
                if 0 <= vni < len(vn):
                    norm = np.array(vn[vni], dtype=np.float32)
                    n_len = np.linalg.norm(norm)
                    norm = norm / n_len if n_len > 1e-8 else fn
                else:
                    norm = fn

                uv = np.array(vt[vti], dtype=np.float32) if 0 <= vti < len(vt) else np.array([0.0, 0.0], dtype=np.float32)

                t = tangent - np.dot(tangent, norm) * norm
                tl = np.linalg.norm(t)
                t = t / tl if tl > 1e-8 else np.array([1.0, 0.0, 0.0], dtype=np.float32)

                verts.extend([pos[0], pos[1], pos[2], norm[0], norm[1], norm[2], t[0], t[1], t[2], uv[0], uv[1]])
                idx_map[key] = len(idx_map)

            indices.append(idx_map[key])

    return np.array(verts, dtype=np.float32), np.array(indices, dtype=np.uint32)


def _perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    d = near - far
    return np.array([[f / aspect, 0, 0, 0], [0, f, 0, 0], [0, 0, (far + near) / d, 2 * far * near / d], [0, 0, -1, 0]], dtype=np.float32)


def _look_at(eye: list[float], center: list[float], up: list[float]) -> np.ndarray:
    e, c, u = (np.array(x, dtype=np.float32) for x in (eye, center, up))
    f = c - e
    f /= np.linalg.norm(f)
    r = np.cross(f, u)
    r /= np.linalg.norm(r)
    uu = np.cross(r, f)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = r
    m[1, :3] = uu
    m[2, :3] = -f
    m[0, 3] = -np.dot(r, e)
    m[1, 3] = -np.dot(uu, e)
    m[2, 3] = np.dot(f, e)
    return m


def _rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m


def _rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4, dtype=np.float32)
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m


class GLViewport(QOpenGLWidget):

    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)

        self._program = None
        self._vao = self._vbo = self._ibo = None
        self._index_count = 0

        self._tex_albedo = None
        self._tex_normal = None
        self._tex_height = None
        self._tex_ao = None
        self._tex_roughness = None
        self._tex_metal = None

        self._mesh = "Cube"
        self._rot_y_val = 0.0
        self._rot_x_val = 0.2
        self._cam_dist = 3.5
        self._auto_rot = True
        self._last_mouse: QPoint | None = None
        self._bump_scale = 0.05
        self._ao_strength = 1.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)

    def initializeGL(self):
        try:
            vert = shaders.compileShader(VERT_SRC, gl.GL_VERTEX_SHADER)
            frag = shaders.compileShader(FRAG_SRC, gl.GL_FRAGMENT_SHADER)
            self._program = shaders.compileProgram(vert, frag)
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            return
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)
        self._upload_mesh()

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)

    def paintGL(self):
        gl.glClearColor(0.12, 0.12, 0.14, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if self._program is not None and self._vao is not None:
            self._render()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse = event.pos()
            self._auto_rot = False

    def mouseMoveEvent(self, event):
        if self._last_mouse and event.buttons() & Qt.MouseButton.LeftButton:
            d = event.pos() - self._last_mouse
            self._rot_y_val += d.x() * 0.01
            self._rot_x_val = max(-1.5, min(1.5, self._rot_x_val + d.y() * 0.01))
            self._last_mouse = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self._last_mouse = None

    def mouseDoubleClickEvent(self, event):
        self._rot_y_val = 0.0
        self._rot_x_val = 0.2
        self._cam_dist = 3.5
        self._auto_rot = True
        self.update()

    def wheelEvent(self, event):
        self._cam_dist = max(1.5, min(12.0, self._cam_dist - event.angleDelta().y() * 0.003))
        self.update()

    def set_mesh(self, name_or_path: str):
        self._mesh = name_or_path
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._upload_mesh()
        finally:
            self.doneCurrent()
        self.update()

    def set_albedo(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_albedo = self._upload_texture(bgr, self._tex_albedo)
        finally:
            self.doneCurrent()
        self.update()

    def set_normal_map(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_normal = self._upload_texture(bgr, self._tex_normal)
        finally:
            self.doneCurrent()
        self.update()

    def set_heightmap(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_height = self._upload_texture(bgr, self._tex_height)
        finally:
            self.doneCurrent()
        self.update()

    def set_ao_map(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_ao = self._upload_texture(bgr, self._tex_ao)
        finally:
            self.doneCurrent()
        self.update()

    def set_roughness_map(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_roughness = self._upload_texture(bgr, self._tex_roughness)
        finally:
            self.doneCurrent()
        self.update()

    def set_metal_map(self, bgr):
        if not self.isValid():
            return
        self.makeCurrent()
        try:
            self._tex_metal = self._upload_texture(bgr, self._tex_metal)
        finally:
            self.doneCurrent()
        self.update()

    def set_bump_scale(self, v: float):
        self._bump_scale = v

    def set_ao_strength(self, v: float):
        self._ao_strength = v

    def set_auto_rotate(self, e: bool):
        self._auto_rot = e

    def _on_tick(self):
        if self._auto_rot:
            self._rot_y_val += 0.008
            self.update()

    def _upload_mesh(self):
        if self._program is None:
            return

        if self._mesh.lower().endswith('.obj') and os.path.exists(self._mesh):
            try:
                vertices, indices = _load_obj(self._mesh)
            except Exception as e:
                print(f"Error loading OBJ mesh: {e}")
                vertices, indices = _build_cube()
        else:
            vertices, indices = _build_sphere() if self._mesh == "Sphere" else _build_cube()

        self._index_count = len(indices)

        if self._vao:
            gl.glDeleteVertexArrays(1, [self._vao])
        if self._vbo:
            gl.glDeleteBuffers(1, [self._vbo])
        if self._ibo:
            gl.glDeleteBuffers(1, [self._ibo])

        self._vao = gl.glGenVertexArrays(1)
        self._vbo = gl.glGenBuffers(1)
        self._ibo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        stride = 11 * 4
        for loc, size, offset in [(0, 3, 0), (1, 3, 12), (2, 3, 24), (3, 2, 36)]:
            gl.glEnableVertexAttribArray(loc)
            gl.glVertexAttribPointer(loc, size, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(offset))

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ibo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        gl.glBindVertexArray(0)

    def _upload_texture(self, bgr: np.ndarray | None, old_tex) -> int | None:
        if old_tex is not None:
            try:
                gl.glDeleteTextures(1, [old_tex])
            except Exception:
                pass
        if bgr is None:
            return None
        h, w = bgr.shape[:2]
        if h <= 0 or w <= 0:
            return None

        rgb = np.ascontiguousarray(bgr[:, :, ::-1], dtype=np.uint8)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, w, h, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, rgb)
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return int(tex)

    def _loc(self, name: str) -> int:
        if self._program is None:
            return -1
        return gl.glGetUniformLocation(self._program, name)

    def _render(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        model = _rot_x(self._rot_x_val) @ _rot_y(self._rot_y_val)
        view = _look_at([0, 0, self._cam_dist], [0, 0, 0], [0, 1, 0])
        proj = _perspective(45.0, w / h, 0.1, 100.0)
        nm3 = np.linalg.inv(model[:3, :3]).T.astype(np.float32)

        gl.glUseProgram(self._program)

        def set_m4(name, mat):
            loc = self._loc(name)
            if loc != -1:
                gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, mat.T)

        def set_m3(name, mat):
            loc = self._loc(name)
            if loc != -1:
                gl.glUniformMatrix3fv(loc, 1, gl.GL_FALSE, mat.T)

        def set_3f(name, x, y, z):
            loc = self._loc(name)
            if loc != -1:
                gl.glUniform3f(loc, x, y, z)

        def set_1f(name, v):
            loc = self._loc(name)
            if loc != -1:
                gl.glUniform1f(loc, v)

        def set_1i(name, v):
            loc = self._loc(name)
            if loc != -1:
                gl.glUniform1i(loc, v)

        set_m4("u_model", model)
        set_m4("u_view", view)
        set_m4("u_proj", proj)
        set_m3("u_normal_mat", nm3)

        set_3f("u_light_dir", 0.5, -0.8, 0.5)
        set_3f("u_light_color", 1.4, 1.35, 1.25)
        set_3f("u_fill_dir", -0.8, -0.2, 0.2)
        set_3f("u_fill_color", 0.4, 0.45, 0.55)
        set_3f("u_rim_dir", 0.0, -0.3, -1.0)
        set_3f("u_rim_color", 0.6, 0.6, 0.7)

        set_3f("u_cam_pos", 0.0, 0.0, self._cam_dist)
        set_1f("u_bump_scale", self._bump_scale)
        set_1f("u_ao_strength", self._ao_strength)

        tex_bindings = [
            (self._tex_albedo, "u_albedo", "u_has_albedo"),
            (self._tex_normal, "u_normal_map", "u_has_normal"),
            (self._tex_height, "u_heightmap", "u_has_height"),
            (self._tex_ao, "u_ao_map", "u_has_ao"),
            (self._tex_roughness, "u_roughness_map", "u_has_roughness"),
            (self._tex_metal, "u_metal_map", "u_has_metal"),
        ]

        for unit, (tex, uname, flag) in enumerate(tex_bindings):
            if tex is not None:
                gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
                gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
                set_1i(uname, unit)
                set_1i(flag, 1)
            else:
                set_1i(flag, 0)

        gl.glBindVertexArray(self._vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self._index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)