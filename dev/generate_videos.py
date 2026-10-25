"""
Gera vídeos animados com efeitos criativos para Pandora S.A.
Renderiza frames com Python + PIL e encoda com ffmpeg.
"""
import subprocess
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# ── Constantes ─────────────────────────────────────────────────────────────

W, H   = 1280, 720
FPS    = 24
SECS   = 5
N      = FPS * SECS          # total de frames

C_ORANGE   = (255, 107, 43)
C_GREEN_HI = (200, 255, 200)
C_GREEN    = (0, 220, 60)
C_WHITE    = (240, 240, 240)
C_GRAY     = (130, 130, 130)
C_DIM      = (55, 55, 65)
C_RED_HI   = (255, 55, 55)
C_BG       = (8, 8, 12)

MATRIX_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*<>[]{}/\\"

BASE = Path(__file__).parent.parent / "mcp-server" / "videos"

VIDEOS = [
    ("ai4csp-fundamental/aula1_introducao.mp4",
     "ai4csp", "AI4CSP — Fundamental Edition", "Aula 1 · Introdução", False),
    ("ai4csp-fundamental/aula5_personalizar.mp4",
     "ai4csp", "AI4CSP — Fundamental Edition", "Aula 5 · Personalizar (no-code)", False),
    ("ai4csp-fundamental/aula5_chaves_labs.mp4",
     "ai4csp", "AI4CSP — Fundamental Edition", "Material Extra: Chaves de API dos Labs", True),
    ("llmas-pentest/aula1_introducao.mp4",
     "llmas", "LLMAS — Pentest Edition", "Aula 1 · Introdução", False),
    ("llmas-pentest/aula2_prompt_injection.mp4",
     "llmas", "LLMAS — Pentest Edition", "Aula 2 · Prompt Injection Attacks", False),
    ("llmas-pentest/aula6_agentic_layer.mp4",
     "llmas", "LLMAS — Pentest Edition", "Aula 6 · Attacking Agentic Layer", True),
    ("ai4csp-webpentest/aula1_webpentest_conversacional.mp4",
     "webpentest", "AI4CSP — Web Pentest Edition", "Aula 1 · WebPentest Conversacional", False),
    ("ai4csp-webpentest/aula4_hackbots101.mp4",
     "webpentest", "AI4CSP — Web Pentest Edition", "Aula 4 · Hackbots 101", False),
    ("ai4csp-webpentest/aula4_hackbots_raw.mp4",
     "webpentest", "AI4CSP — Web Pentest Edition", "Aula 4 · Hackbots RAW [BRUTO]", True),
]


# ── Fonts ───────────────────────────────────────────────────────────────────

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/truetype/firacode/",
    "/usr/share/fonts/truetype/liberation/",
]

_FONTS = {
    "mono":       "FiraCode-Regular.ttf",
    "mono_bold":  "FiraCode-Bold.ttf",
    "sans":       "DejaVuSans.ttf",
    "sans_bold":  "DejaVuSans-Bold.ttf",
}

_fcache: dict = {}


def F(key: str, size: int) -> ImageFont.FreeTypeFont:
    k = (key, size)
    if k in _fcache:
        return _fcache[k]
    name = _FONTS[key]
    for d in _FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            f = ImageFont.truetype(str(p), size)
            _fcache[k] = f
            return f
    f = ImageFont.load_default()
    _fcache[k] = f
    return f


# ── Helpers ─────────────────────────────────────────────────────────────────

def text_x(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return (W - (bb[2] - bb[0])) // 2


def glow_text(img: Image.Image, text: str, pos: tuple, font,
              color: tuple, glow: tuple, radius: int = 10) -> Image.Image:
    """Escreve texto com efeito de brilho (glow) via blur."""
    rgba = img.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text(pos, text, fill=(*glow, 220), font=font)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    rgba.alpha_composite(layer)
    ImageDraw.Draw(rgba).text(pos, text, fill=(*color, 255), font=font)
    return rgba.convert("RGB")


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ── Efeito 1: Matrix Rain (AI4CSP Fundamental) ─────────────────────────────

class MatrixEffect:
    CHAR_W = 15
    CHAR_H = 19

    def __init__(self, seed: int):
        rng = random.Random(seed)
        self._font = F("mono", self.CHAR_H - 3)
        ncols = W // self.CHAR_W + 2
        nrows = H // self.CHAR_H + 25

        self._cols = []
        for _ in range(ncols):
            start  = rng.randint(-nrows, N + nrows)
            fpr    = rng.choice([1, 1, 1, 2, 2, 3])    # frames por linha
            trail  = rng.randint(6, 20)
            chars  = [rng.choice(MATRIX_CHARS) for _ in range(nrows + trail)]
            self._cols.append((start, fpr, trail, chars))
        self._nrows = nrows

    def render(self, f: int) -> Image.Image:
        img  = Image.new("RGB", (W, H), (0, 10, 0))
        draw = ImageDraw.Draw(img)

        for ci, (start, fpr, trail, chars) in enumerate(self._cols):
            x        = ci * self.CHAR_W
            head_row = (f - start) // fpr

            for t in range(trail):
                row = head_row - t
                if row < 0 or row >= self._nrows:
                    continue
                y = row * self.CHAR_H
                if y >= H:
                    continue

                ch = chars[(row * 7 + ci * 13 + f // 4) % len(chars)]

                if t == 0:
                    color = (220, 255, 220)
                elif t == 1:
                    color = (80, 255, 80)
                else:
                    r = (trail - t) / trail
                    color = (0, int(160 * r * r), 0)

                draw.text((x, y), ch, fill=color, font=self._font)

        return img


# ── Efeito 2: Glitch / Scan Lines (LLMAS Pentest) ──────────────────────

class GlitchEffect:
    CHAR_SZ = 11

    def __init__(self, seed: int):
        rng = random.Random(seed)
        self._font = F("mono", self.CHAR_SZ)
        self._pitch = self.CHAR_SZ          # largura por coluna (monospace)
        self._lh    = self.CHAR_SZ + 2      # altura por linha

        ncols = W // self._pitch + 2
        nrows = H // self._lh + 4
        # Grid de hex que serve como fundo
        self._grid = [
            [f"{rng.randint(0, 255):02X}" for _ in range(ncols)]
            for _ in range(nrows)
        ]
        self._nrows = nrows

        # Eventos de glitch: faixa horizontal que "desloca"
        self._glitches = [
            {
                "start": rng.randint(0, N - 8),
                "y":     rng.randint(0, H - 80),
                "h":     rng.randint(6, 60),
                "dx":    rng.randint(-160, 160),
                "dur":   rng.randint(2, 10),
            }
            for _ in range(18)
        ]

        # Instantes de aberração RGB intensa
        self._rgb_bursts = {rng.randint(0, N - 1) for _ in range(8)}

    def render(self, f: int) -> Image.Image:
        img  = Image.new("RGB", (W, H), (3, 4, 16))
        draw = ImageDraw.Draw(img)

        # Fundo: hex scrollando para cima
        scroll = (f * 1) % (self._nrows * self._lh)
        for ri in range(self._nrows + 1):
            y = ri * self._lh - scroll
            if y < -self._lh or y > H:
                continue
            row = self._grid[ri % self._nrows]
            for ci, ch in enumerate(row):
                seed_v = (ri * 17 + ci * 31 + f // 5) % 38
                b = 16 + seed_v
                draw.text((ci * self._pitch, y), ch, fill=(0, b, b + 4), font=self._font)

        # Beam de scan (linha brilhante descendo)
        scan_y = int((f / N) * H * 1.3) % H
        for dy in range(-18, 19):
            y = scan_y + dy
            if 0 <= y < H:
                a = max(0.0, 1.0 - abs(dy) / 18.0)
                v = int(a * a * 55)
                draw.line([(0, y), (W, y)], fill=(0, v // 2, v))

        # Faixas de glitch
        for g in self._glitches:
            age = f - g["start"]
            if not (0 <= age < g["dur"]):
                continue
            fade = 1.0 - age / g["dur"]
            dx   = int(g["dx"] * fade)
            y1, y2 = g["y"], min(H, g["y"] + g["h"])
            for y in range(y1, y2):
                v = int(fade * 75)
                r = int(fade * 110) if (y + f) % 3 == 0 else 0
                draw.line([(max(0, dx), y), (min(W, W + dx), y)], fill=(r, 0, v))

        # Aberração RGB (chromatica)
        shift = 5 if f in self._rgb_bursts else (2 if (f % 15) < 3 else 0)
        if shift:
            rc, gc, bc = img.split()
            rc = ImageChops.offset(rc,  shift, 0)
            bc = ImageChops.offset(bc, -shift, 0)
            img = Image.merge("RGB", (rc, gc, bc))

        return img


# ── Efeito 3: Radar Sweep (AI4CSP Web Pentest) ─────────────────────────────

class RadarEffect:
    def __init__(self, seed: int):
        rng   = random.Random(seed)
        self.cx, self.cy = W // 2, H // 2
        self.max_r = min(W, H) // 2 - 30
        self._sweep_speed = 2 * math.pi / N    # volta completa em 5 s

        # Blips: posição polar aleatória
        self._blips = []
        for _ in range(14):
            angle  = rng.uniform(0, 2 * math.pi)
            radius = rng.uniform(0.2, 0.92) * self.max_r
            self._blips.append((angle, radius))

    def _polar_to_xy(self, angle: float, r: float):
        return (
            self.cx + int(r * math.cos(angle)),
            self.cy + int(r * math.sin(angle)),
        )

    def render(self, f: int) -> Image.Image:
        img  = Image.new("RGB", (W, H), (0, 7, 3))
        draw = ImageDraw.Draw(img)

        # Grid de fundo (linhas finas)
        for x in range(0, W, 55):
            draw.line([(x, 0), (x, H)], fill=(0, 14, 6))
        for y in range(0, H, 55):
            draw.line([(0, y), (W, y)], fill=(0, 14, 6))

        # Anéis de alcance
        for ratio in [0.25, 0.5, 0.75, 1.0]:
            r = int(self.max_r * ratio)
            bb = [self.cx - r, self.cy - r, self.cx + r, self.cy + r]
            draw.ellipse(bb, outline=(0, 38, 16), width=1)

        # Linhas de rumo (cada 45°)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            ex, ey = self._polar_to_xy(rad, self.max_r)
            draw.line([(self.cx, self.cy), (ex, ey)], fill=(0, 28, 12))

        # Ângulo atual do sweep
        sweep = f * self._sweep_speed

        # Cauda do sweep (trilha que vai apagando)
        TRAIL_STEPS = 48
        for step in range(TRAIL_STEPS, 0, -1):
            a    = sweep - step * math.radians(2.8)
            fade = (TRAIL_STEPS - step) / TRAIL_STEPS
            g    = int(fade * fade * 110)
            ex, ey = self._polar_to_xy(a, self.max_r)
            draw.line([(self.cx, self.cy), (ex, ey)],
                      fill=(0, g, int(g * 0.3)), width=max(1, int(fade * 3)))

        # Linha do sweep (borda brilhante)
        ex, ey = self._polar_to_xy(sweep, self.max_r)
        draw.line([(self.cx, self.cy), (ex, ey)], fill=(60, 255, 120), width=2)

        # Blips
        for blip_angle, blip_r in self._blips:
            diff = (sweep - blip_angle) % (2 * math.pi)
            if diff < 0.08:
                brightness = 1.0
            else:
                brightness = max(0.0, 1.0 - diff * 1.4 / (2 * math.pi))
            if brightness < 0.04:
                continue
            bx, by = self._polar_to_xy(blip_angle, blip_r)
            size   = int(brightness * 6) + 2
            g      = int(brightness * 255)
            r_v    = int(brightness * 80)
            draw.ellipse([bx - size, by - size, bx + size, by + size],
                         fill=(r_v, g, r_v // 2))

        return img


# ── Efeito 4: Confidencial (fundo vermelho pulsante) ───────────────────────

class ConfidentialEffect:
    def __init__(self, seed: int):
        pass    # sem estado aleatório necessário

    def render(self, f: int) -> Image.Image:
        t     = f / N
        pulse = 0.5 + 0.5 * math.sin(t * math.pi * 6)   # ~3 Hz
        bg_r  = int(12 + pulse * 30)
        img   = Image.new("RGB", (W, H), (bg_r, 2, 2))
        draw  = ImageDraw.Draw(img)

        # Scanlines
        for y in range(0, H, 4):
            draw.line([(0, y), (W, y)], fill=(0, 0, 0))

        # Ruído de estática sutil nas bordas
        for _ in range(80):
            sx = random.randint(0, W - 1)
            sy = random.randint(0, H - 1)
            v  = random.randint(30, 80)
            draw.point((sx, sy), fill=(v, 0, 0))

        return img


# ── Overlay de texto ────────────────────────────────────────────────────────

def add_overlay(img: Image.Image, course: str, lesson: str,
                confidential: bool, f: int) -> Image.Image:
    t    = f / N
    fade = min(1.0, t * 2.5)    # fade-in em ~0.4 s
    draw = ImageDraw.Draw(img)

    f_brand   = F("sans_bold", 20)
    f_course  = F("sans_bold", 46)
    f_lesson  = F("sans",      30)
    f_footer  = F("sans",      17)
    f_warn    = F("sans_bold", 68)
    f_warn_sm = F("sans_bold", 26)

    # ── "PANDORA S.A." — topo esquerdo ──
    brand_color = lerp_color((0, 0, 0), C_ORANGE, fade)
    draw.text((32, 22), "PANDORA S.A.", fill=brand_color, font=f_brand)

    if confidential:
        # Piscar: on nos primeiros 12 frames de cada ciclo de 24 (0.5 s a 24fps)
        blink_on = (f % 24) < 12

        if blink_on:
            warn = "⚠  CONFIDENCIAL  ⚠"
            wx   = text_x(draw, warn, f_warn)
            wy   = H // 2 - 65
            # Glow vermelho
            img  = glow_text(img, warn, (wx, wy), f_warn,
                             C_RED_HI, (100, 0, 0), radius=14)
            draw = ImageDraw.Draw(img)

        # Nome da lição
        lc    = lerp_color((0, 0, 0), (180, 80, 80), fade)
        lx    = text_x(draw, lesson, f_lesson)
        draw.text((lx, H // 2 + 30), lesson, fill=lc, font=f_lesson)

        # Rodapé de aviso
        footer = "USO INTERNO  —  NÃO DISTRIBUIR"
        fc     = lerp_color((0, 0, 0), (160, 40, 40), fade)
        fx     = text_x(draw, footer, f_warn_sm)
        draw.text((fx, H - 55), footer, fill=fc, font=f_warn_sm)

    else:
        # Nome do curso com glow
        cc  = lerp_color((0, 0, 0), C_WHITE, fade)
        cx  = text_x(draw, course, f_course)
        cy  = H // 2 - 52
        img = glow_text(img, course, (cx, cy), f_course, cc, (30, 30, 30), radius=12)
        draw = ImageDraw.Draw(img)

        # Nome da lição
        lc  = lerp_color((0, 0, 0), C_GRAY, fade)
        lx  = text_x(draw, lesson, f_lesson)
        draw.text((lx, H // 2 + 18), lesson, fill=lc, font=f_lesson)

        # Rodapé
        footer = "plataforma de cursos de segurança"
        fc     = lerp_color((0, 0, 0), C_DIM, fade)
        fx     = text_x(draw, footer, f_footer)
        draw.text((fx, H - 42), footer, fill=fc, font=f_footer)

    return img


# ── Encoder ─────────────────────────────────────────────────────────────────

def encode(out: Path, frames, beep: bool = False):
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "pipe:0",
    ]

    if beep:
        # Beep de 800 Hz, 0.1 s ligado a cada 0.5 s
        cmd += [
            "-f", "lavfi",
            "-i", f"sine=frequency=800:sample_rate=44100:duration={SECS}",
            "-af", "volume='if(lt(mod(t,0.5),0.1),0.5,0)':eval=frame",
            "-c:a", "aac", "-b:a", "64k", "-shortest",
        ]

    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "21",
        str(out),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for frame_img in frames:
        proc.stdin.write(frame_img.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou (código {proc.returncode}): {out.name}")


# ── Main ─────────────────────────────────────────────────────────────────────

def make_video(out: Path, course_id: str, course: str, lesson: str, confidential: bool):
    seed = hash(course_id + lesson) & 0xFFFF

    if confidential:
        effect = ConfidentialEffect(seed)
    elif course_id == "ai4csp":
        effect = MatrixEffect(seed)
    elif course_id == "llmap":
        effect = GlitchEffect(seed)
    else:
        effect = RadarEffect(seed)

    def frames():
        for i in range(N):
            bg = effect.render(i)
            yield add_overlay(bg, course, lesson, confidential, i)

    encode(out, frames(), beep=confidential)


def main():
    import time
    for rel, course_id, course, lesson, confidential in VIDEOS:
        out = BASE / rel
        tag = "CONFIDENCIAL" if confidential else course_id.upper()
        print(f"[{tag}] {out.name} ...", end=" ", flush=True)
        t0 = time.time()
        make_video(out, course_id, course, lesson, confidential)
        print(f"{time.time() - t0:.1f}s")
    print("\nTodos os vídeos gerados!")


if __name__ == "__main__":
    main()
