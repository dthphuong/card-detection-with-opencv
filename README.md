
# Card detection with OpenCV

A Python code that allowed detect namecard, business card, ATM/VISA card border using OpenCV library


## Installation

You need to install OpenCV version 3.x.x or 4.x.x and Google Vision SDK (take a look in References)

## Run

Clone the project

```bash
  git clone https://github.com/dthphuong/card-detection-with-opencv.git
```

Go to the project directory

```bash
  cd card-detection-with-opencv
```

Install packages
```bash
pip install -r requirements.txt
```

Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file that contains your service account key

Let's rock

```bash
  python run.py -i c8.jpg -o o8.jpg
```


## References
- https://cloud.google.com/vision/docs/quickstart-client-libraries
- https://cloud.google.com/vision/docs/ocr#vision_text_detection-python

## Author
**Dương Trần Hà Phương (Mr.)** - CEO [Công ty TNHH FPO](https://fpo.vn)
- Email: [phuongduong@fpo.vn](mailto:phuongduong@fpo.vn)
- Website: [https://phuongduong.fpo.vn](https://phuongduong.fpo.vn)
- Gitlab: [@dthphuong1](https://gitlab.com/dthphuong1)
- Github: [@dthphuong](https://github.com/dthphuong)
