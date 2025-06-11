# Face Access Control

Sistema de control de acceso basado en reconocimiento facial usando:

- Flask (Python)
- Librería `face_recognition`
- ESP32-CAM como cliente de captura

## Endpoints API

- `POST /api/verify-face`: Verifica coincidencia de rostro enviado desde ESP32-CAM
- `POST /api/register-face`: Registra una nueva imagen en la base

## Autor

Jhosimar Guerrero - Proyecto 
