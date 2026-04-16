import requests
from bs4 import BeautifulSoup
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.io.VideoFileClip import VideoFileClip

# Rutas relativas para portabilidad (Render/GitHub)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
STATIC_DIR = os.path.join(BASE_DIR, "static")
FONT_PATH = os.path.join(ASSETS_DIR, "Adobe Garamond Pro Semibold.otf")

def ensure_font(size=50):
    try:
        if os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, size)
        else:
            # Fallback for local dev if assets not local
            return ImageFont.load_default()
    except:
        return ImageFont.load_default()

def create_animated_video_from_data(top_5, map_path, output_mp4=None):
    if output_mp4 is None:
        output_mp4 = os.path.join(STATIC_DIR, "historia_lluvias.mp4")
        
    WIDTH, HEIGHT = 1080, 1920
    FPS = 12
    
    font_title = ensure_font(75)
    font_subtitle = ensure_font(55)
    font_items = ensure_font(65)
    font_footer = ensure_font(45)

    bg_video_path = os.path.join(STATIC_DIR, "background_rain.mp4")
    
    if not os.path.exists(bg_video_path):
        return create_animated_video_legacy(top_5, map_path, output_mp4)
    
    bg_clip = VideoFileClip(bg_video_path)
    bg_clip = bg_clip.resized(height=HEIGHT) 
    bg_clip = bg_clip.cropped(x_center=bg_clip.size[0]/2, width=WIDTH)
    
    DURATION = min(bg_clip.duration, 10) 
    total_frames = int(FPS * DURATION)
    
    map_img_static = None
    if map_path and os.path.exists(map_path):
        map_img_static = Image.open(map_path)
        target_w = 920
        w_percent = (target_w / float(map_img_static.size[0]))
        target_h = int((float(map_img_static.size[1]) * float(w_percent)))
        map_img_static = map_img_static.resize((target_w, target_h), Image.Resampling.LANCZOS)

    frames_images = []
    for f in range(total_frames):
        t = f / FPS
        bg_frame_np = bg_clip.get_frame(t)
        frame = Image.fromarray(bg_frame_np)
        
        overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 110))
        frame.paste(overlay, (0,0), overlay)
        draw = ImageDraw.Draw(frame)
        
        draw.text((WIDTH//2, 180), "Lluvias en la región núcleo", font=font_title, fill="white", anchor="mm")
        draw.text((WIDTH//2, 260), "Mayores registros de las últimas 24 h", font=font_subtitle, fill="#dddddd", anchor="mm")
        
        y_text = 420
        for i, d in enumerate(top_5):
            if t >= (1.0 + i * 0.4):
                line = f"{i+1}. {d['localidad']}: {d['mm']} mm"
                draw.text((140, y_text), line, font=font_items, fill="white")
            y_text += 105
        
        if t >= 3.5 and map_img_static:
            paste_x = (WIDTH - map_img_static.size[0]) // 2
            paste_y = 1000
            shadow = Image.new('RGBA', map_img_static.size, (0,0,0,150))
            frame.paste(shadow, (paste_x+10, paste_y+10), shadow)
            frame.paste(map_img_static, (paste_x, paste_y))
            
        draw.text((WIDTH//2, 1820), "Más información en bcr.com.ar", font=font_footer, fill="#cccccc", anchor="mm")
        frames_images.append(np.array(frame))

    bg_clip.close()
    
    final_clip = ImageSequenceClip(frames_images, fps=FPS)
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)
    final_clip.write_videofile(output_mp4, codec="libx264", audio=False, logger=None)
    return output_mp4

def create_animated_video_legacy(top_5, map_path, output_mp4):
    WIDTH, HEIGHT = 1080, 1920
    FPS = 10
    DURATION = 6
    bg_color = (15, 45, 80)
    font_title = ensure_font(75)
    font_items = ensure_font(65)
    
    frames_images = []
    for f in range(FPS * DURATION):
        t = f / FPS
        frame = Image.new('RGB', (WIDTH, HEIGHT), color=bg_color)
        draw = ImageDraw.Draw(frame)
        draw.text((WIDTH//2, 200), "Lluvias en la región núcleo", font=font_title, fill="white", anchor="mm")
        
        y_text = 450
        for i, d in enumerate(top_5):
            if t >= (0.5+i*0.3):
                line = f"{i+1}. {d['localidad']}: {d['mm']} mm"
                draw.text((150, y_text), line, font=font_items, fill="white")
            y_text += 100
            
        frames_images.append(np.array(frame))

    clip = ImageSequenceClip(frames_images, fps=FPS)
    clip.write_videofile(output_mp4, codec="libx264", audio=False, logger=None)
    return output_mp4

def get_rainfall_metadata():
    url_lluvias = "https://www.bcr.com.ar/es/mercados/gea/estaciones-meteorologicas/red-de-estaciones-meteorologicas"
    r = requests.get(url_lluvias, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(r.text, 'html.parser')

    tables = soup.find_all('table')
    table = tables[1] if len(tables) > 1 else tables[0]
    
    data = []
    rows = table.find_all('tr')
    for row in rows[2:]:
        cols = row.find_all('td')
        if len(cols) >= 8:
            estacion = cols[0].text.strip()
            precip_str = cols[4].text.strip()
            try:
                precip_val = float(precip_str.replace(',', '.'))
                if precip_val > 0: 
                    data.append({'localidad': estacion, 'mm': precip_val})
            except ValueError:
                pass

    data.sort(key=lambda x: x['mm'], reverse=True)
    top5 = data[:5]

    texto_tweet = "☔️ Registros de lluvias acumuladas en la región núcleo (Últimas 24h):\n\n"
    for d in top5:
        texto_tweet += f"- {d['localidad']}: {d['mm']} mm\n"
    texto_tweet += "\nMapas y más info en:\nhttps://www.bcr.com.ar/es/mercados/gea/clima/clima-gea/lluvias"

    url_mapa_base = "https://www.bcr.com.ar/es/mercados/gea/clima/clima-gea/lluvias"
    r_img = requests.get(url_mapa_base, headers={'User-Agent': 'Mozilla/5.0'})
    soup_img = BeautifulSoup(r_img.text, 'html.parser')
    
    imagen_url = None
    for img in soup_img.find_all('img'):
        src = img.get('src')
        if src and ('lluvia' in src.lower() or 'acumula' in src.lower()):
            if not src.startswith('http'):
                src = "https://www.bcr.com.ar" + src
            imagen_url = src
            break
            
    imagen_local_path = None
    if imagen_url:
        os.makedirs(STATIC_DIR, exist_ok=True)
        r_down = requests.get(imagen_url, headers={'User-Agent': 'Mozilla/5.0'})
        imagen_local_name = 'mapa_lluvias.jpg'
        imagen_local_path = os.path.join(STATIC_DIR, imagen_local_name)
        with open(imagen_local_path, 'wb') as f:
            f.write(r_down.content)
        return top5, texto_tweet, f"/static/{imagen_local_name}"

    return top5, texto_tweet, None
