# AI App Builder Android Beta

This Android client connects to the existing FastAPI backend.

## Important
Do NOT put OPENAI_API_KEY inside the APK.

Configure a reachable backend URL in the app, for example:

- Local network: http://192.168.1.10:8000
- Public deployment: https://your-backend.example.com

`localhost` on the Android phone does not mean the computer running FastAPI.
