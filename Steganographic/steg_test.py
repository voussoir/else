import steganographic
import time
import traceback
def encode(i, s):
    try:
        steganographic.encode(i, s)
    except:
        traceback.print_exc()
        time.sleep(0.1)
        print()
def decode(i):
    try:
        steganographic.decode(i)
    except:
        traceback.print_exc()
        time.sleep(0.1)
        print()
#encode('examples\\steg_notbigenough.png', 'examples\\steg_thats_advertising.mp4')
#encode('examples\\steg_supersmall.png', 'examples\\steg_thats_advertising.mp4')
#encode('examples\\steg_18pixels.png', 'examples\\steg_thats_advertising.mp4')
#encode('examples\\steg_19pixels.png', 'examples\\steg_thats_advertising.mp4')
#encode('examples\\steg_20pixels.png', 'examples\\steg_empty.txt')
#encode('examples\\steg_20pixels.png', 'examples\\steg_text.txt')
#encode('examples\\steg_33pixels.png', 'examples\\steg_text.txt')
#encode('examples\\steg_33pixels.png', 'examples\\steg_text_noex')

#decode('examples\\steg_33pixels (steg_text_txt).png')
#decode('examples\\steg_trespassing (3bp_thats_advertising_mp4).png')

encode('examples\\trespassing.png', 'examples\\thats_advertising.mp4')
decode('examples\\trespassing (thats_advertising_mp4).png')