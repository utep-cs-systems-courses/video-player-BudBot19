import threading
import cv2
import numpy as np
import base64
import queue
import os

from threading import Thread

class extractFrames(Thread):
    def __init__(self, fileName, outputBuffer, empty, full):
        Thread.__init__(self)
        self.fileName = fileName
        self.outputBuffer = outputBuffer
        self.maxFramesToLoad = 9999
        self.empty = empty
        self.full = full
        
    def run(self):
        #frame count
        count = 0

        vidcap = cv2.VideoCapture(self.fileName)

        success,image = vidcap.read()

        print(f'Reading frame {count} {success}')

        while success and count < self.maxFramesToLoad:
            self.empty.acquire()
            success, jpgImage = cv2.imencode('.jpg', image)
            self.outputBuffer.put(image)
            self.full.release()

            jpgAsText = base64.b64encode(jpgImage)


            success, image = vidcap.read()
            print(f'Reading frame {count} {success}')
            count += 1

        self.outputBuffer.put(None)
        self.full.release()

        print('Frame extraction complete')



class displayFrames(Thread):
    def __init__(self, inputBuffer, empty, full):
        Thread.__init__(self)
        self.inputBuffer = inputBuffer
        self.empty = empty
        self.full = full
        
    def run(self):
        count = 0

        while True:
            self.full.acquire()
            frame = self.inputBuffer.get()
            self.empty.release()

            if frame is None:
                break
            
            print(f'Displaying frame {count}')

            cv2.imshow('Video', frame)
            if cv2.waitKey(42) and 0xFF == ord("q"):
                break


            count += 1

        print('Finished displaying all frames')
        cv2.destroyAllWindows()


class convertToGrayScale(Thread):
    def __init__(self, inputBuffer, input_empty, input_full,
                 outputBuffer, output_empty, output_full):
        Thread.__init__(self)
        self.inputBuffer = inputBuffer
        self.input_empty = input_empty
        self.input_full = input_full
        self.outputBuffer = outputBuffer
        self.output_empty = output_empty
        self.output_full = output_full
        
    def run(self):
        count = 0

        while True:
            self.input_full.acquire()
            frame = self.inputBuffer.get()
            self.input_empty.release()

            if frame is None:

                self.output_empty.acquire()
                self.outputBuffer.put(None)
                self.output_full.release()
                
                break
            

            print(f'Converting frame {count}')

            grayscaleFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            self.output_empty.acquire()
            self.outputBuffer.put(grayscaleFrame)
            self.output_full.release()
            count += 1

        print('Finished Conversion')


##main
filename = 'clip.mp4'
buffer_size = 10

extractionQueue = queue.Queue()
displayQueue =queue.Queue()

##for extract to convert
empty = threading.Semaphore(buffer_size)
full = threading.Semaphore(0)

#for convert to display
empty2 = threading.Semaphore(buffer_size)
full2 = threading.Semaphore(buffer_size)

extract = extractFrames(filename, extractionQueue, empty, full)
gray = convertToGrayScale(extractionQueue, empty, full,
                          displayQueue, empty2, full2)
display = displayFrames(displayQueue, empty2, full2)

extract.start()
gray.start()
display.start()

extract.join()
gray.join()
display.join()

        
        
