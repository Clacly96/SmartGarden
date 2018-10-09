import numpy as np
import sys,os,datetime,piexif
import cv2.cv2 as cv2
from moviepy.editor import *

def ridimensiona(img,frame_height,frame_width):
    dim_esatta="" # "a" se alt=frame_height "l" altrimenti
    alt,larg=img.shape[:2]
    if alt>larg:
        nuova_alt=frame_height
        nuova_larg=larg*frame_height/alt
        dim_esatta="a"
        if nuova_larg>frame_width:
            alt=nuova_alt
            larg=nuova_larg
            nuova_larg=frame_width
            nuova_alt=alt*frame_width/larg
            dim_esatta="l"
    elif larg>alt:
        nuova_larg=frame_width
        nuova_alt=alt*frame_width/larg
        dim_esatta="l"
        if nuova_alt>frame_height:
            alt=nuova_alt
            larg=nuova_larg
            nuova_alt=frame_height
            nuova_larg=larg*frame_height/alt
            dim_esatta="a"

    img_r = cv2.resize(img, (int(nuova_larg),int(nuova_alt)), interpolation = cv2.INTER_AREA)
    if dim_esatta=="a":
        dim_bordo=frame_width-img_r.shape[1]
        frame=cv2.copyMakeBorder(img_r,top=0,bottom=0, left=int(dim_bordo/2), right=int(dim_bordo/2),borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    elif dim_esatta=="l":
        dim_bordo=frame_height-img_r.shape[0]
        frame=cv2.copyMakeBorder(img_r,top=int(dim_bordo/2),bottom=int(dim_bordo/2), left=0, right=0,borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    # Nel caso in cui il frame con il bordo ha dimensioni diverse dovute ad arrotondamenti ad int, viene ridimensionato con le dimensioni esatte
    if frame.shape[0]!=frame_height or frame.shape[1]!=frame_width:
        frame=cv2.resize(frame, (frame_width,frame_height), interpolation = cv2.INTER_AREA)
    return frame

def crea_video(inizio_dt,fine_dt,percorso,fps):
    if percorso[-1]!="/":
        percorso=percorso+"/"
    frame_width=1280
    frame_height=720


    out = cv2.VideoWriter('video_out.mp4',cv2.VideoWriter_fourcc(*'H264'), fps, (frame_width,frame_height))

    vettore_file_data={}
    for filename in os.listdir(percorso):
        exif_dict = piexif.load(percorso+filename)
        data=exif_dict["Exif"][36867].decode()
        data_dt=datetime.datetime.strptime(data,"%Y:%m:%d %H:%M:%S")
        if data_dt>=inizio_dt and data_dt<=fine_dt:
            vettore_file_data[data_dt]=filename

    for key in sorted(vettore_file_data):

        if(grayscale==1):
            img=cv2.imread(percorso+vettore_file_data[key],cv2.IMREAD_GRAYSCALE)
        else:
            img=cv2.imread(percorso+vettore_file_data[key],cv2.IMREAD_ANYCOLOR)
        # shape restituisce (altezza,larghezza,num_canali)
        #calcolo nuove dimensioni
        if img.shape[0]>frame_height or img.shape[1]>frame_width:
            frame=ridimensiona(img,frame_height,frame_width)
        else:
            frame=img

        dimtesto=cv2.getTextSize(str(key),cv2.FONT_HERSHEY_SIMPLEX,1,1)[0] # (larghezza,altezza)
        altezza_rect=dimtesto[1]+10
        cv2.rectangle(frame,(0,frame_height),(frame_width,frame_height-altezza_rect),(0,0,0),-1)
        cv2.putText(frame,str(key),(int((frame_width-dimtesto[0])/2),int(frame_height-(altezza_rect-dimtesto[1])/2)),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)

        out.write(frame)


    out.release()
    if(gif==1):
        clip = VideoFileClip("video_out.mp4")
        clip.write_gif("video_out.gif")
    #    os.remove("video_out.mp4") vedere se necessario, in fase di test no

if __name__=="__main__":
    try:
        percorso=str(sys.argv[1])
        inizio=str(sys.argv[2])
        fine=str(sys.argv[3])
        fps=int(sys.argv[4])
        grayscale=int(sys.argv[5])
        gif=int(sys.argv[6])
        inizio_dt=datetime.datetime.strptime(inizio,"%Y-%m-%d")
        fine_dt=datetime.datetime.strptime(fine,"%Y-%m-%d")
    except ValueError:
        print("Inserire le date nel formato AAAA-MM-GG")
        sys.exit(1)
    except IndexError:
        print("Attenzione, inserire i seguenti parametri: path_name, data_inizio (AAAA-MM-GG), data_fine (AAAA-MM-GG), fps, grayscale, gif")
        sys.exit(1)

    crea_video(inizio_dt,fine_dt,percorso,fps)
    sys.exit(0)
