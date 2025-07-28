import cv2

def extract_contour_points(image_path: str) -> list[tuple[int,int]]:
    """
    Reads image, extracts external contours, returns list of pixel coordinates.
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pts = []
    for cnt in cnts:
        for p in cnt:
            pts.append((int(p[0][0]), int(p[0][1])))
    return pts