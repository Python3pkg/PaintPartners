import pygame,copy,math,colorsys,queue,Window
import re
from pygame.locals import *
from threading import Thread

def parse_data(data):
    return [_f for _f in re.split('[{}]', data) if _f]

class PixelProcessThread(Thread):
    def __init__(self,image,clientWindow):
        super(PixelProcessThread, self).__init__()
        self.daemon = True
        self.running = True
        self.q = queue.Queue()
        self.image = image
        self.clientWindow = clientWindow
    def add(self,data):
        self.q.put(data)
    def stop(self):
        self.running = False
    def process_mouse(self,data):
        clientName = ""
        mouseX = ""
        mouseY = ""
        count = 0

        for i in data:
            if i == "$": #clientName
                for a in range(25):
                    try:
                        if data[count+a+1] != ";":
                            clientName += data[count+a+1]
                        else:
                            break
                    except:
                        break
            elif i == ";": #mouseX
                for r in range(4):
                    try:
                        if data[count+r].isdigit():
                            mouseX += data[count+r]
                    except:
                        break
            elif i == ":": #mouseY
                for q in range(4):
                    try:
                        if data[count+q].isdigit():
                            mouseY += data[count+q]
                    except:
                        break
            count += 1
        if mouseX != "" and mouseY != "":
            self.clientWindow.clients_icons[clientName].set_pos((int(mouseX),int(mouseY)))

    def process_pixels(self,data):
        clientName = ""
        mouseX = ""
        mouseY = ""
        x = ""
        y = ""
        hexColor = ""
        count = 0
        for i in data:
            process = False
            if i == "$": #clientName
                for a in range(25):
                    try:
                        if data[count+a+1] != ";":
                            clientName += data[count+a+1]
                        else:
                            break
                    except:
                        break
            elif i == ";": #mouseX
                for r in range(4):
                    try:
                        if data[count+r].isdigit():
                            mouseX += data[count+r]
                    except:
                        break
            elif i == ":": #mouseY
                for q in range(4):
                    try:
                        if data[count+q].isdigit():
                            mouseY += data[count+q]
                    except:
                        break
            elif i == ".":
                for s in range(4):
                    try:
                        if data[count+s].isdigit():
                            x += data[count+s]
                    except:
                        x = ""
                        break
            elif i == ",":
                for t in range(4):
                    try:
                        if data[count+t].isdigit():
                            y += data[count+t]
                    except:
                        y = ""
                        break
            elif i == "#":
                for u in range(6):
                    try:
                        hexColor += data[count+u+1]
                    except:
                        hexColor = ""
                        break
                process = True
            if process == True:
                if x != "" and y != "" and hexColor != "":
                    self.image.pixels[int(x),int(y)] = pygame.Color("#"+hexColor)
                x = ""
                y = ""
                hexColor = ""
 
            count += 1  
        self.image.image = self.image.pixels.make_surface()
        if mouseX != "" and mouseY != "":
            self.clientWindow.clients_icons[clientName].set_pos((int(mouseX),int(mouseY)))
        
    def process_brushes(self,data):
        clientName = ""
        mouseX = ""
        mouseY = ""
        x = ""
        y = ""
        hexColor = ""
        radius = 0
        radiusStr = ""
        brushType = ""
        count = 0
        for i in data:
            process = False
            if i == "$": #clientName
                for a in range(25):
                    try:
                        if data[count+a+1] != ";":
                            clientName += data[count+a+1]
                        else:
                            break
                    except:
                        break
            elif i == ";": #mouseX
                for r in range(4):
                    try:
                        if data[count+r].isdigit():
                            mouseX += data[count+r]
                    except:
                        break
            elif i == ":": #mouseY
                for q in range(4):
                    try:
                        if data[count+q].isdigit():
                            mouseY += data[count+q]
                    except:
                        break
            elif i == ".":
                for s in range(4):
                    try:
                        if data[count+s].isdigit():
                            x += data[count+s]
                    except:
                        x = ""
                        break
            elif i == ",":
                for t in range(4):
                    try:
                        if data[count+t].isdigit():
                            y += data[count+t]
                    except:
                        y = ""
                        break
            elif i == "#":
                for u in range(6):
                    try:
                        hexColor += data[count+u+1]
                    except:
                        hexColor = ""
                        break
            elif i == "|":
                for v in range(6):
                    try:
                        brushType += data[count+v+1]
                    except:
                        brushType = ""
                        break
            elif i == "`":
                for w in range(6):
                    try:
                        if data[count+w+1].isdigit():
                            radiusStr += data[count+w+1]
                        else:
                            radius = int(radiusStr)
                            process = True
                            break
                    except IndexError:
                        radius = int(radiusStr)
                        process = True
                        break
                    except not IndexError:
                        radius = 0
                        break
            if process == True:
                if x != "" and y != "" and hexColor != "" and brushType != "" and radius != 0:
                    
                    self.image.paint(radius,brushType,(int(x)-radius),(int(y)-radius),hexColor)
                    x = ""
                    y = ""
                    hexColor = ""
                    radiusStr = ""
                    radius = 0
                    brushType = ""

                    
            count += 1
        self.image.image = self.image.pixels.make_surface()
        if mouseX != "" and mouseY != "":
            self.clientWindow.clients_icons[clientName].set_pos((int(mouseX),int(mouseY)))
        
    def run(self):
        while self.running == True:
            if not self.q.empty():
                data = self.q.get(block=True)

                if "_PIXELDATA_" in data:
                    self.process_pixels(data[11:])
                elif "_BRUSHDATA_" in data:
                    self.process_brushes(data[11:])
                elif "_MOUSEDATA_" in data:
                    self.process_mouse(data[11:])

class ColorWheel(object):
    def __init__(self,pos,r):
        self.pos = pos
        self.radius = r
        self.image = pygame.Surface((r,r))
        self.image.fill((255,255,255))
        self.pos = pos
        self.image_rect = pygame.Rect(0,0,r,r)
        self.image_rect.topleft = (pos[0]+1,pos[1])
        self.image_rect_border = pygame.Rect(0,0,r+2,r+2)
        self.image_rect_border.topleft = (pos[0],pos[1]-1)

        self.pixels = pygame.PixelArray(self.image)

        for x in range(r):
            for y in range(r):
                side1 = (x - (r/2))
                side2 = (y - (r/2))
                side3 = math.sqrt((side1**2) + (side2**2))
                hue = (math.atan2(side2,side1)+3.14159)/(3.14159*2)
                if side3 <= (r/2):
                    rgb = colorsys.hsv_to_rgb(hue,(side3/(r/2)),1)
                    self.pixels[x,y] = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
                
        self.image = self.pixels.make_surface()

    def is_click(self,events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False
    
    def is_mouse_over(self,mousePos):
        if mousePos[0] < self.image_rect.x or mousePos[0] > self.image_rect.x + self.image_rect.w or mousePos[1] < self.image_rect.y or mousePos[1] > self.image_rect.y + self.image_rect.h:
            return False
        return True
    
    def update(self,events,mousePos,currentColor,valueSlider):
        if valueSlider.moving == True:
            for event in events:
                if event.type == MOUSEBUTTONUP:
                    value = valueSlider.get_value()
                    if value > 1:
                        value = 1
                    elif value < 0:
                        value = 0

                    pi = 3.14159
                    pi2 = 3.14159*2

                    rad2 = self.radius/2
                    
                    for x in range(self.radius):
                        for y in range(self.radius):    
                            side1 = (x - rad2)
                            side2 = (y - rad2)
                            side3 = math.sqrt((side1**2) + (side2**2))
                            hue = (math.atan2(side2,side1)+pi)/pi2
                            if side3 <= rad2:
                                rgb = colorsys.hsv_to_rgb(hue,side3/rad2,value)
                                self.pixels[x,y] = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
                    self.image = self.pixels.make_surface()
        
        if self.is_mouse_over(mousePos) == True:
            if self.is_click(events) == True:
                currentColor.color_fill = self.get_color(mousePos[0],mousePos[1])

    def get_color(self,mouseX,mouseY):
        try:
            xPos = int(mouseX - self.pos[0])
            yPos = int(mouseY - self.pos[1])
            return self.image.unmap_rgb(self.pixels[xPos,yPos])
        except:
            return (0,0,0)
                        
    def draw(self,screen):
        pygame.draw.rect(screen,(0,0,0),self.image_rect_border)
        screen.blit(self.image,self.image_rect)

    
class PaintBrush(object):
    def __init__(self,pos,r,brushType="Circle"):
        self.radiusOld = r/2
        self.radius = r/2
        self.scale = 1.0
        self.pos = pos
        self.image = pygame.Surface((r,r))
        self.image.fill((255,255,255))
        self.image_rect = pygame.Rect(0,0,r,r)
        self.image_rect.midtop = (pos[0]+1,pos[1])
        self.image_rect_border = pygame.Rect(0,0,r+2,r+2)
        self.image_rect_border.midtop = (pos[0]+1,pos[1]-1)
        self.selected = False
        self.pixels = pygame.PixelArray(self.image)
        self.type = brushType
        for x in range(r):
            for y in range(r):
                side1 = (x - self.radius)
                side2 = (y - self.radius)
                side3 = math.sqrt((side1**2) + (side2**2))
                if side3 <= self.radius or self.type == "Square":
                    self.pixels[x,y] = (0,0,0)
        self.image = self.pixels.make_surface()
        del self.pixels

    def paint_pixels(self,startX,startY,paintImage,currentColor):
        col = (currentColor.color_fill[2],currentColor.color_fill[1],currentColor.color_fill[0])
        for i in range(self.radius*2):
            for j in range(self.radius*2):
                side1 = (i - self.radius)
                side2 = (j - self.radius)
                side3 = math.sqrt((side1**2) + (side2**2))
                if side3 <= self.radius or self.type == "Square":
                    if startX+i > 0 and startX+i < paintImage.width and startY+j > 0 and startY+j < paintImage.height:
                        paintImage.pixels[startX+i,startY+j] = col
                        paintImage.pixel_buffer[(startX+i,startY+j)] = paintImage.rgb_to_hex((col[0],col[1],col[2]))
                        
    def paint_brushes(self,startX,startY,paintImage,currentColor):
        col = (currentColor.color_fill[2],currentColor.color_fill[1],currentColor.color_fill[0])
        paintImage.brush_buffer[(startX+self.radius,startY+self.radius)] = paintImage.rgb_to_hex((col[0],col[1],col[2])) + "|" + self.type + "`" + str(self.radius)
        for i in range(self.radius*2):
            for j in range(self.radius*2):
                side1 = (i - self.radius)
                side2 = (j - self.radius)
                side3 = math.sqrt((side1**2) + (side2**2))
                if side3 <= self.radius or self.type == "Square":
                    if startX+i > 0 and startX+i < paintImage.width and startY+j > 0 and startY+j < paintImage.height:
                        paintImage.pixels[startX+i,startY+j] = col
            
    def is_click(self,events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False
    
    def is_mouse_over(self,mousePos):
        if mousePos[0] < self.image_rect.x or mousePos[0] > self.image_rect.x + self.image_rect.w or mousePos[1] < self.image_rect.y or mousePos[1] > self.image_rect.y + self.image_rect.h:
            return False
        return True
    
    def update(self,events,mousePos,sizeSlider):
        if sizeSlider.moving == True:
            for event in events:
                if event.type == MOUSEBUTTONUP:
                    value = sizeSlider.get_value() + 0.5
                    self.scale = 1.0 + value
                    self.radius = int(1.0 + (self.radiusOld * self.scale))
    
    def draw(self,screen):
        if self.selected == True:
            pygame.draw.rect(screen,(100,100,255),self.image_rect_border)
        screen.blit(self.image,self.image_rect)
    
class PaintImage(object):
    def __init__(self,program,pos,w,h):
        self.program = program
        self.image = pygame.Surface((w,h))
        self.width = w
        self.height = h
        self.image.fill((255,255,255))
        self.pos = pos
        self.image_rect = pygame.Rect(0,0,w,h)
        self.image_rect.topleft = (pos[0]+1,pos[1])
        self.image_rect_border = pygame.Rect(0,0,w+2,h+2)
        self.image_rect_border.topleft = (pos[0],pos[1]-1)

        self.pixels = pygame.PixelArray(self.image.copy())

        self.pixel_buffer = {}
        self.brush_buffer = {}

        self.timer = 0.0

        self.process_thread = PixelProcessThread(self,program.window_clients)
        self.process_thread.start()
        
    def tostring(self):
        imgdata = pygame.image.tostring(self.image,"RGB")
        return imgdata
    
    def fromstring(self,data):
        self.image = pygame.image.frombuffer(data,(self.width,self.height),"RGB")
        self.pixels = pygame.PixelArray(self.image.copy())
        
    def resize(self,size,location):
        self.pos = location
        self.image_rect.topleft = (self.pos[0]+1,self.pos[1])
        self.image_rect_border.topleft = (self.pos[0],self.pos[1]-1)
 
    def is_click(self,events):
        mouseState = pygame.mouse.get_pressed()
        if mouseState[0] == 1:
            return True
        return False

    def paint(self,radius,brushType,startX,startY,hexColor):
        for i in range(radius*2):
            for j in range(radius*2):
                side1 = (i - radius)
                side2 = (j - radius)
                side3 = math.sqrt((side1**2) + (side2**2))
                if side3 <= radius or brushType == "Square":
                    if startX+i > 0 and startX+i < self.width and startY+j > 0 and startY+j < self.height:
                        self.pixels[startX+i,startY+j] = pygame.Color("#"+hexColor)

    def hex_to_rgb(self,value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))
    def rgb_to_hex(self,rgb):
        return '%02x%02x%02x' % rgb
    def convert_pixel_buffer_to_string(self,mousePos):
        string = "$" + self.program.client.username + ";" + str(mousePos[0]) + ":" + str(mousePos[1])
        if len(self.pixel_buffer) == 0:
            return string
        for key,value in self.pixel_buffer.items():
            string += "." + str(key[0]) + "," + str(key[1]) + "#" + value
        return string
    def convert_brush_buffer_to_string(self,mousePos):
        string = "$" + self.program.client.username + ";" + str(mousePos[0]) + ":" + str(mousePos[1])
        if len(self.brush_buffer) == 0:
            return string
        for key,value in self.brush_buffer.items():
            string += "." + str(key[0]) + "," + str(key[1]) + "#" + value
        return string
    def convert_mouse_pos(self,mousePos):
        string = "$" + self.program.client.username + ";" + str(mousePos[0]) + ":" + str(mousePos[1])
        return string
    
    def is_mouse_over(self,mousePos):
        if mousePos[0] < self.image_rect.x or mousePos[0] > self.image_rect.x + self.image_rect.w or mousePos[1] < self.image_rect.y or mousePos[1] > self.image_rect.y + self.image_rect.h:
            return False
        return True
        
    def update(self,events,elapsed,mousePos,currentColor,client,canEdit=True,currentBrush=None):
        self.timer += float(elapsed/1000.0)

        if not self.is_click(events):
            if self.timer > 0.5:
                string1 = self.convert_mouse_pos(mousePos)
                client.send_message("{" + "_MOUSEDATA_" + string1 + "}")
                self.timer = 0
        
        if not canEdit:
            return
        
        x = mousePos[0] - self.pos[0]
        y = mousePos[1] - self.pos[1]
        if self.is_mouse_over(mousePos):
            if self.is_click(events):
                if currentBrush != None:
                    startX = x - currentBrush.radius
                    startY = y - currentBrush.radius
                    
                    #currentBrush.paint_pixels(startX,startY,self,currentColor)
                    currentBrush.paint_brushes(startX,startY,self,currentColor)

                self.image = self.pixels.make_surface()
 
        if not self.pixel_buffer and not self.brush_buffer:
            return

        if self.timer > 0.5:
            #string = self.convert_pixel_buffer_to_string(mousePos)
            string = self.convert_brush_buffer_to_string(mousePos)
            
            #client.send_message("{" + "_PIXELDATA_" + string + "}")
            client.send_message("{" + "_BRUSHDATA_" + string + "}")
            
            self.pixel_buffer.clear()
            self.brush_buffer.clear()
            self.timer = 0

    
    def draw(self,screen):
        pygame.draw.rect(screen,(0,0,0),self.image_rect_border)
        screen.blit(self.image,self.image_rect)
        
class ColorIcon(pygame.sprite.Sprite):
    def __init__(self,programSize,pos,w=5,h=5,borderColor=(0,0,0),fillColor=(225,225,225)):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pos
        self.width = w
        self.height = h
        self.color_border = borderColor
        self.color_fill = fillColor

        self.rect_border = None
        self.rect = pygame.Rect(0,0,self.width,self.height)
        self.rect.topleft = self.pos

        self.rect_border = pygame.Rect(0,0,self.width+2,self.height+2)
        self.rect_border.topleft = (self.pos[0]-1,self.pos[1]-1)

    def is_click(self,events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False
    
    def is_mouse_over(self,mousePos):
        if mousePos[0] < self.rect.x or mousePos[0] > self.rect.x + self.rect.w or mousePos[1] < self.rect.y or mousePos[1] > self.rect.y + self.rect.h:
            return False
        return True
    
    def update(self,events,mousePos):
        pass
    
    def draw(self,screen):
        pygame.draw.rect(screen,self.color_border,self.rect_border)
        pygame.draw.rect(screen,self.color_fill,self.rect)
