import base64
import cv2

with open("encoded.txt","w") as file:
    for i in range(20):
        path = "demo-images/image" + str(i) + ".jpeg"
        image = cv2.imread(path)
        _, buffer = cv2.imencode('.jpg', image)
        base64_string = base64.b64encode(buffer).decode('utf-8')
        file.write(base64_string + "\n")
file.close()