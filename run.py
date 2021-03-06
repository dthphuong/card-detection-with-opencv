import argparse
import cv2
import sys
import numpy as np
from google.cloud import vision
import io
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./config.json"

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", required = True, help = "Path to the input image")
ap.add_argument("-o", "--output", required = True, help = "Path to the output image")
ap.add_argument("-d", "--debug", required = False, help = "Debug status")
args = vars(ap.parse_args())

DEBUG = args["debug"] == 'True'
cv_version = cv2.__version__
rectangle_epsilon = 0.5
position_epsilon = 0.25
canny_threshold = 100
stdW = 25; stdH = 25
padding = 25

def distance(v1, v2):
    return np.sqrt(np.sum((v1 - v2) ** 2))

# Find contours
def findContours(image):
    # Convert image to GrayScale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # using the Canny edge detector
    edge = cv2.Canny(blurred, canny_threshold, canny_threshold * 2)

    # apply a dilation
    dilated = cv2.dilate(edge, None, iterations=1)

    if DEBUG:
        pass
        # cv2.imshow("Blurred", blurred)
        # cv2.imshow("Dilation", dilated)
        # cv2.imshow("Canny edge detector", edge)

    # Find contours
    if (cv_version[0] == '4'):
        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return [contours, hierarchy]

def getTextBoudingBox(path):
    """Get bounding box of all text in image"""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if (len(texts) > 0):
        minLenTopLeft = 100000
        maxLenBottomRight = 0
        return [(vertex.x, vertex.y) for vertex in texts[0].bounding_poly.vertices]
    else:
        return [(0,0), (0,0), (0,0), (0,0)]

    if response.error.message:
        return [(0,0), (0,0), (0,0), (0,0)]

def filterBoundingBox(contours):
    boundingBoxes = [list(cv2.boundingRect(cnt)) for cnt in contours]
    return list(filter(lambda box: (box[2] > stdW and box[3] > stdH), boundingBoxes))

# Find the Largest Rectangle
def findTheLargestRect(contours, imageW, imageH):
    xMin = 0; yMin = 0; xMax = 0; yMax = 0; resW = 0; resH = 0

    points = getTextBoudingBox(args['input'])
    xA_ = points[0][0]; yA_ = points[0][1]; xC_ = points[2][0]; yC_ = points[2][1]
    # print(points)

    if (points == [(0,0), (0,0), (0,0), (0,0)]):
        # Can't find text
        return [0, 0, imageW, imageH]
    else:
        # Found text
        xA = 0; yA = 0; xC = 0; yC = 0;
        wMax = 0; hMax = 0; sMax = 0

        # finding the largest rectangle
        boundingBoxes = filterBoundingBox(contours)
        # print(boundingBoxes)
        for [x, y, w, h] in boundingBoxes:
            if (w * h >= sMax): #and h/w >= rectangle_epsilon
                sMax = w * h
                wMax = w; hMax = h
                xA = x; yA = y
                xC = xA + wMax; yC = yA + hMax

        # finding the union rectangle
        xMin = xA if xA < xA_ else xA_
        yMin = yA if yA < yA_ else yA_
        xMax = xC if xC > xC_ else xC_
        yMax = yC if yC > yC_ else yC_
        resW = xMax - xMin
        resH = yMax - yMin

        # refine rectangle with rectangle_epsilon
        if (resH / resW < rectangle_epsilon):
            yMin = (yMin - int((resW/2 - resH)/2)) if (yMin - int((resW/2 - resH)/2) > 0) else yMin
            resH = (resH + int((resW/2 - resH))) if (resH + int((resW/2 - resH)) < imageH) else imageH

        # add padding around
        xMin = (xMin - padding) if (xMin - padding > 0) else 0
        yMin = (yMin - padding) if (yMin - padding > 0) else 0
        resW = (resW + padding*2) if (resW + padding*2 < imageW) else imageW
        resH = (resH + padding*2) if (resH + padding*2 < imageH) else imageH

        return [xMin, yMin, resW, resH]

def findGreenRect(contours, imageW, imageH):
    xMin = 0
    yMin = 0
    xMax = 0
    yMax = 0
    resW = 0
    resH = 0

    # Found text
    xA = 0
    yA = 0
    xC = 0
    yC = 0
    wMax = 0
    hMax = 0
    sMax = 0

    # finding the largest rectangle
    boundingBoxes = filterBoundingBox(contours)
    # print(boundingBoxes)
    for [x, y, w, h] in boundingBoxes:
        if (w * h >= sMax ): #and h/w >= rectangle_epsilon
            sMax = w * h
            wMax = w
            hMax = h
            xA = x
            yA = y
            xC = xA + wMax
            yC = yA + hMax

    return [xA, yA, wMax, hMax]

#================================================================================================
# MAIN PROGRAM
#================================================================================================
# Read image file
print('=======DEBUG = {}======='.format(DEBUG))
print("##########################################################")
print('process file {}'.format(args["input"]))
image = cv2.imread(args["input"])
if image is None:
    sys.exit("File not found!")

contours, hierarchy = findContours(image)

points = getTextBoudingBox(args["input"])

[x, y, w, h] = findTheLargestRect(contours, image.shape[1], image.shape[0])

# =====Crop by the largest contours=====
cropImgage = image[y:y+h, x:x+w]
cv2.imwrite(args["output"], cropImgage)
print("##########################################################")



if DEBUG:
    # =====Final rect=====
    print('Final rect: {}'.format([x, y, w, h]))
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 5)

    # =====Show original image and its size=====
    # cv2.imshow("Original", image)
    # print((image.shape[0], image.shape[1]))

    # =====contours info=====
    # print(len(contours))

    # =====the largest contours params=====
    # print([x, y, w, h])

    # =====Draw contours=====
    # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # cv2.imshow('Final edge', image)

    # =====Draw all contours=====
    # drawing = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
    # for i in range(len(contours)):
    #     if i == 0:
    #         # print(contours[i])
    #         cv2.drawContours(drawing, contours, i, (0,0,255), 2, cv2.LINE_8, hierarchy, 0)
    #     else:
    #         cv2.drawContours(drawing, contours, i, (0,255,0), 2, cv2.LINE_8, hierarchy, 0)
    # cv2.imshow('all contours', drawing)

    # =====Draw contours bounding boxes=====
    # cv2.drawContours(image, contours, -1, (0,0,255), 3, cv2.LINE_8, hierarchy, 0)
    bounding_boxes = filterBoundingBox(contours)
    for bbox in bounding_boxes:
         [x , y, w, h] = bbox
         cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 255), 2)
    # cv2.imshow('bounding boxes', image)


    # =====Green rect=====
    [xx, yy, ww, hh] = findGreenRect(contours, image.shape[1], image.shape[0])
    print('Green rect: {}'.format([xx, yy, ww, hh]))
    cv2.rectangle(image, (xx, yy), (xx + ww, yy + hh), (0, 255, 0), 5)

    # =====Draw bounding boxes by GG Vison=====
    cv2.rectangle(image, points[0], points[2], (255, 0, 0), 2)
    # cv2.imshow('GG Vison', image)

    # =====Crop final image=====
    # cv2.imshow('Crop image', cropImgage)

    cv2.imwrite('./debug/' + args["input"], image)

    cv2.waitKey(0)