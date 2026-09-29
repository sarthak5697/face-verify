import sys
from deepface import DeepFace

def main():
    if len(sys.argv) != 3:
        print("Usage: python verify.py <image1> <image2>")
        sys.exit(1)

    img1, img2 = sys.argv[1], sys.argv[2]

    try:
        result = DeepFace.verify(
            img1_path=img1,
            img2_path=img2,
            model_name="ArcFace",        # face-embedding model
            detector_backend="retinaface",   # face detector ("opencv" is faster but less accurate)
            distance_metric="cosine",
        )
    except ValueError as e:
        print(f"Error: {e}")
        if e.__cause__:
            print(f"Reason: {e.__cause__}")
        sys.exit(1)

    print("Same person :", "YES" if result["verified"] else "NO")
    print(f"Distance    : {result['distance']:.4f}  (lower = more similar)")
    print(f"Threshold   : {result['threshold']:.4f}  (below this = same person)")
    print(f"Model       : {result['model']}")
    print(f"Time taken  : {result['time']}s")

if __name__ == "__main__":
    main()