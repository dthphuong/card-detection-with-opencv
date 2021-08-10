import argparse
import cv2
import sys
import numpy as np
import pytesseract

DEBUG = False
cv_version = cv2.__version__
rectangle_epsilon = 0.5
position_epsilon = 0.25

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", required = True, help = "Path to the input image")
ap.add_argument("-o", "--output", required = True, help = "Path to the output image")
args = vars(ap.parse_args())


# Find the Largest Rectangle
def findTheLargestRect(contours, imageW, imageH):
    xMax = 0
    yMax = 0
    wMax = 0
    hMax = 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if (w >= wMax and h >= hMax and h/w >= rectangle_epsilon):
            wMax = w
            hMax = h
            xMax = x
            yMax = y

    if DEBUG:
        pass
        # print([xMax, yMax, wMax, hMax])
        # print(wMax/imageW)

    if (wMax/imageW > position_epsilon):
        return [xMax, yMax, wMax, hMax]
    else:
        return [0, 0, imageW, imageH]

# Find contours
def findContours(image):
    # Convert image to GrayScale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur image
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # apply Otsu's automatic thresholding which automatically determines
    # the best threshold value
    (T, threshInv) = cv2.threshold(blurred, 200, 255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # using the Canny edge detector
    edge = cv2.Canny(blurred, T*0.5, T)
    # edge = autoCanny(blurred, sigma=float(args["sigma"]))

    # apply a dilation
    dilated = cv2.dilate(edge, None, iterations=1)

    if DEBUG:
        cv2.imshow("Blurred", blurred)
        cv2.imshow("Dilation", dilated)
        cv2.imshow("Canny edge detector", edge)
        cv2.imshow("Threshold", threshInv)
        print('----')
        print(T)
        print('----')
    else:
        pass


    # Find contours
    # ONLY get parrent contours with param RETR_EXTERNAL
    if (cv_version[0] == '4'):
        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return [contours, hierarchy]

def filterContoursWithTextOnly(contours):
    res = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        cropImgage = image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(cropImgage)
        if (text != ''):
            res.append([x, y, w, h])

    return res

def findTheLargestBoundingBox(contours, imageW, imageH):
    xMin = imageW
    yMin = imageH
    xMax = -1
    yMax = -1

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        cropImgage = image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(cropImgage)
        if (text != ''):
            xMin = x if x < xMin else xMin
            xMax = (x + w) if (x + w) > xMax else xMax
            yMin = y if y < yMin else yMin
            yMax = (y + h) if (y + h) > yMax else yMax

    return [xMin, yMin, xMax - xMin, yMax - yMin]

#================================================================================================
# MAIN PROGRAM
#================================================================================================
# Read image file
image = cv2.imread(args["input"])
if image is None:
    sys.exit("File not found!")

contours, hierarchy = findContours(image)

[x, y, w, h] = findTheLargestBoundingBox(contours, image.shape[1], image.shape[0])

# =====Crop by the largest contours=====
cropImgage = image[y:y+h, x:x+w]
cv2.imwrite(args["output"], cropImgage)




if DEBUG:

    # =====Show original image and its size=====
    cv2.imshow("Original", image)
    print((image.shape[0], image.shape[1]))

    # =====contours info=====
    print(len(contours))

    # =====the largest contours params=====
    print([x, y, w, h])

    # =====Draw contours=====
    drawing = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow('Final edge', image)

    # =====Draw all contours=====
    for i in range(len(contours)):
        if i == 0:
            # print(contours[i])
            cv2.drawContours(drawing, contours, i, (0,0,255), 2, cv2.LINE_8, hierarchy, 0)
        else:
            cv2.drawContours(drawing, contours, i, (0,255,0), 2, cv2.LINE_8, hierarchy, 0)
    cv2.imshow('all contours', drawing)

    # =====Draw contours bounding boxes=====
    cv2.drawContours(image, contours, -1, (0,0,255), 3, cv2.LINE_8, hierarchy, 0)
    bounding_boxes = [cv2.boundingRect(cnt) for cnt in contours]
    for bbox in bounding_boxes:
         [x , y, w, h] = bbox
         cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow('bounding boxes', image)

    # =====Crop final image=====
    cv2.imshow('Crop image', cropImgage)

    cv2.waitKey(0)