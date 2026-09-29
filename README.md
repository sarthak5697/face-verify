# Face Verify

Face verification service for the interview assessment tool. It compares two photos and reports whether they show the same person, using [DeepFace](https://github.com/serengil/deepface) (ArcFace model, RetinaFace detector) behind a FastAPI HTTP API.

## Requirements
- Windows 10 or 11
- Python 3.10 (tested with 3.10.8). 3.10.11 is the last 3.10 release with a Windows installer: https://www.python.org/downloads/release/python-31011/. Tick **Add python.exe to PATH** during install.
- Git: https://git-scm.com/download/win
- Internet on first start: about 250 MB of model weights download to `%USERPROFILE%\.deepface`

## Setup on a fresh machine
```powershell
git clone https://github.com/sarthak5697/face-verify.git C:\src\face-verify
cd C:\src\face-verify
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```
Clone to a short path such as `C:\src`. TensorFlow's deep folder structure can exceed the Windows 260-character path limit.

`setup.ps1` finds Python, creates `venv`, and installs the exact versions from `requirements-lock.txt`. No venv activation is needed.

## Run
```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```
Open http://localhost:8000/docs. The first start takes a few minutes while the models download and load.

To accept requests from other machines (for example the .NET app on another server):
```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 -HostAddress 0.0.0.0
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status and model in use |
| POST | `/v1/verify` | Two image files (multipart form: `image1`, `image2`) |
| POST | `/v1/verify/base64` | Two base64 images in JSON |

Full contract and a test page: http://localhost:8000/docs

Quick test from PowerShell:
```powershell
curl.exe -X POST http://localhost:8000/v1/verify -F "image1=@photo1.jpg" -F "image2=@photo2.jpg"
```

## Configuration
Set these environment variables before `run.ps1` to change the defaults:

| Variable | Default | Meaning |
|---|---|---|
| `FACE_MODEL` | `ArcFace` | Face recognition model |
| `FACE_DETECTOR` | `retinaface` | Face detector (`opencv` is faster but less accurate) |
| `MAX_IMAGE_MB` | `10` | Upload size limit per image |

## Command-line check
```powershell
.\venv\Scripts\python.exe verify.py path\to\photo1.jpg path\to\photo2.jpg
```

## Dependencies
- `requirements-lock.txt`: exact versions tested on Windows with Python 3.10. `setup.ps1` uses it.
- `requirements.txt`: direct dependencies only. `setup.ps1` uses it on other Python versions. On Linux/macOS:
  `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Keep `opencv-python` below 5. OpenCV 5.0 wheels don't include the Haar cascade files DeepFace needs.
- After changing dependencies, regenerate the lock file:
  `venv\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 requirements-lock.txt`

## Troubleshooting
| Problem | Fix |
|---|---|
| "running scripts is disabled on this system" | Start scripts with `powershell -ExecutionPolicy Bypass -File ...` as shown above |
| pip fails with a long path or "No such file or directory" error | Clone to a shorter path such as `C:\src\face-verify` |
| `422 NO_FACE_DETECTED` | Use a clear, front-facing photo |
| Windows Firewall prompt with `-HostAddress 0.0.0.0` | Allow on Private networks only |
| No internet on the target machine | Copy `%USERPROFILE%\.deepface` from a machine that has already run the service |
