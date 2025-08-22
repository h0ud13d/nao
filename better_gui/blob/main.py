import cv2
import numpy as np

""" OUT OF FRAME"""
# at a, red circle is not recognized
# at b, looks good 
# at c, looks generally good other than shitty lighting 
# at d, looks good


""" GRID """
# at 3, red cicrle isnt recognized
# at 4, 
filepath = "grid/4.jpg"
dir = filepath.split('/')[0]+'/'

image = cv2.imread(filepath)
if image is None:
    print("Error: Could not read the image. Please check the file path.")
    exit()

image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

color_ranges = {
    'Yellow': ([20, 100, 100], [30, 255, 255]),
    'Blue': ([100, 100, 100], [130, 255, 255]),
    'Red': ([0, 100, 100], [10, 255, 255])  # Note: Red might need two ranges
}

# min area is 3k bcs of small shapes on top of the orange 3x3 grid, they are roughly 2.5k - 10k
def detect_shapes(image, min_area=10000):
    detected_objects = []
    cnt = 1

    for color, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(image_hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                
                if len(approx) == 3:
                    shape = "Triangle"
                elif len(approx) == 4:
                    shape = "Rectangle"
                else:
                    shape = "Circle"
                
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                else:
                    cX, cY = 0, 0

                x_values = [point[0][0] for point in approx]
                y_values = [point[0][1] for point in approx]

                detected_objects.append({
                    "number": cnt,
                    "shape": shape,
                    "color": color,
                    "position": (cX, cY),
                    "perimeter": perimeter, 
                    "area": area,
                    "approx_vertices": approx.tolist(),  # Store vertices as a list
                    "x_values": x_values,  # Store x coordinates
                    "y_values": y_values,  # Store y coordinates
                    "description": f"{color} {shape} at {cX - 20, cY - 20} with a shape of {area}"
                })
                
                cv2.drawContours(image_rgb, [contour], 0, (0, 255, 0), 2)
                cv2.putText(image_rgb, str(cnt), (cX - 20, cY - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 3)
                #cv2.putText(image_rgb, str("HERE"), (620, 1104), cv2.FONT_HERSHEY_SIMPLEX, 5, (0,0,0), 3)
                cnt += 1

    return detected_objects

detected_objects = detect_shapes(image)

cv2.imwrite(f'{dir}detected_shapes.png', cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))

for obj in detected_objects:
    print(f"Object #{obj['number']} ({obj['shape']}) - X values: {obj['x_values']}, Y values: {obj['y_values']}")

print("Detected Objects:")
for obj in detected_objects:
    print(f"#{obj['number']} is {obj['description']}")

print('\n\n')
max_obj = max(detected_objects, key=lambda x: x['area'])
x_min, x_max = min(max_obj['x_values']), max(max_obj['x_values'])
y_min, y_max = min(max_obj['y_values']), max(max_obj['y_values'])

print(f"x_min: {x_min}, x_max: {x_max}, y_min: {y_min}, y_max: {y_max}")

top_left = (x_min, y_min)
bottom_right = (x_max, y_max)

cropped = image[y_min:y_max, x_min:x_max]

cv2.imwrite(f'{dir}cropped_object.png', cropped)
