from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from rembg import remove, new_session
import os
C="/home/user/AIVidGen/experiments/ai_story/refs/cast"; OUT="/home/user/AIVidGen/experiments/ai_story/refs/stills_p2"; os.makedirs(OUT,exist_ok=True)
W,H=768,1344
sess=new_session("isnet-general-use")
bg=Image.open("experiments/ai_story/refs/plate_morning.png").convert("RGB")
def cut(name,flip=False):
    p=f"cut_{name}_{int(flip)}.png"
    if not os.path.exists(p):
        im=Image.open(f"{C}/{name}.jpg").convert("RGB")
        if flip: im=ImageOps.mirror(im)
        remove(im,session=sess).save(p)
    return Image.open(p)
def grade(rgba):
    rgb=rgba.convert("RGB"); a=rgba.getchannel("A").filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    rgb=ImageEnhance.Brightness(rgb).enhance(0.9); rgb=ImageEnhance.Contrast(rgb).enhance(1.05)
    r,g,b=rgb.split(); rgb=Image.merge("RGB",(r.point(lambda v:v*0.97),g,b.point(lambda v:min(255,v*1.03))))
    rgb.putalpha(a); return rgb
def fg_back(name, side):
    # Listener's back: bigger than the speaker, close to camera, only the edge of the
    # head and one shoulder inside the frame (~12%), tilted toward the speaker.
    im=cut(name)                                     # full 768x1376 back view, RGBA
    al=im.getchannel("A")
    # head = top 22% of the figure; find its left/right extent from the alpha
    bb=al.getbbox(); top=bb[1]
    head=al.crop((0,top,im.width,top+int((bb[3]-top)*0.18))).getbbox()
    s=3.0
    big=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    big=big.rotate(6 if side=="L" else -6, resample=Image.BICUBIC, center=(big.width//2, int(top*s)))
    rgb=ImageEnhance.Brightness(big.convert("RGB")).enhance(0.5); rgb=ImageEnhance.Color(rgb).enhance(0.7); rgb.putalpha(big.getchannel("A"))
    big=rgb.filter(ImageFilter.GaussianBlur(13))
    edge = head[2]*s if side=="L" else head[0]*s      # head edge facing the speaker
    target = W*0.20 if side=="L" else W*0.80
    x = int(target-edge)
    y = int(H*0.12 - top*s)
    return big,(x,y)
def make(id_, speaker, flip, listener, side):
    out=bg.copy(); sp=grade(cut(speaker,flip)); s=0.76
    sp=sp.resize((int(sp.width*s),int(sp.height*s)),Image.LANCZOS)
    out.paste(sp,((W-sp.width)//2+(110 if side=="L" else -110),H-sp.height+20),sp)
    f,pos=fg_back(listener,side); out.paste(f,pos,f); out.save(f"{OUT}/{id_}.png"); print(id_,flush=True)
jobs=[("P2_L03","eleanor_34",True,"priya_back","L"),("P2_L05","eleanor_smug",False,"priya_back","L"),
("P2_L08","eleanor_angry",False,"priya_back","L"),("P2_L11","eleanor_shock",False,"priya_back","L"),
("P2_L04","priya_34",True,"eleanor_back","R"),("P2_L06","priya_34",True,"eleanor_back","R"),
("P2_L09","priya_smug",False,"eleanor_back","R"),("P2_L12","priya_smile",False,"eleanor_back","R"),
("P2_L07","ethan_sad",False,"priya_back","L"),("P2_L10","ethan_34",True,"priya_back","L")]
for j in jobs: make(*j)
ims=[Image.open(f"{OUT}/{j[0]}.png").resize((192,336)) for j in jobs]
sheet=Image.new("RGB",(960,672))
for i,im in enumerate(ims): sheet.paste(im,((i%5)*192,(i//5)*336))
sheet.save("sheet.jpg")
