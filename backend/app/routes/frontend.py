from __future__ import annotations

import os

from flask import Blueprint, send_from_directory, request


frontend_bp = Blueprint("frontend", __name__)


def _frontend_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend"))


@frontend_bp.route("/")
def index():
    return send_from_directory(_frontend_root(), "index.html")


@frontend_bp.route("/styles.css")
def styles():
    return send_from_directory(_frontend_root(), "styles.css")


@frontend_bp.route("/app.js")
def app_js():
    return send_from_directory(_frontend_root(), "app.js")

@frontend_bp.route("/v4/")
@frontend_bp.route("/v4/<path:filename>")
def v4_files(filename="index.html"):
    return send_from_directory(os.path.join(_frontend_root(), "v4"), filename)

@frontend_bp.route("/confirm")
def confirm_ui():
    token = request.args.get("token", "")
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirm Account - Spectrum Eng V4</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body {{
                background-color: #0f1115;
                color: #e6edf3;
                font-family: 'Inter', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .card {{
                background: #161b22;
                border: 1px solid #30363d;
                padding: 2rem;
                border-radius: 8px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                text-align: center;
            }}
            input {{
                background: #0d1117;
                border: 1px solid #30363d;
                color: white;
                padding: 0.75rem;
                margin: 1rem 0;
                border-radius: 6px;
                width: 100%;
                box-sizing: border-box;
            }}
            button {{
                background: #238636;
                color: white;
                border: 1px solid rgba(240, 246, 252, 0.1);
                padding: 0.75rem;
                width: 100%;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
            }}
            button:hover {{ background: #2ea043; }}
            .logo {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 1.5rem; color: #fff; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">Spectrum Eng V4</div>
            <h2>Set your Password</h2>
            <p style="color: #8b949e;">Confirm your account by setting a secure password.</p>
            <form id="confirmForm">
                <input type="password" id="password" placeholder="New Password" required minlength="6">
                <button type="submit">Confirm Account</button>
            </form>
            <p id="msg" style="margin-top: 1rem; font-size: 0.9rem;"></p>
        </div>
        <script>
            document.getElementById('confirmForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const pwd = document.getElementById('password').value;
                const btn = e.target.querySelector('button');
                const msg = document.getElementById('msg');
                
                btn.disabled = true;
                btn.innerText = "Processing...";
                
                try {{
                    const res = await fetch('/api/auth/confirm', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ token: "{token}", password: pwd }})
                    }});
                    const data = await res.json();
                    
                    if (res.ok) {{
                        msg.style.color = '#2ea043';
                        msg.innerText = "Account confirmed! Redirecting...";
                        setTimeout(() => window.location.href = '/v4/', 2000);
                    }} else {{
                        msg.style.color = '#ff6b6b';
                        msg.innerText = data.error || "Failed to confirm";
                        btn.disabled = false;
                        btn.innerText = "Confirm Account";
                    }}
                }} catch (err) {{
                    msg.style.color = '#ff6b6b';
                    msg.innerText = "Network error";
                    btn.disabled = false;
                    btn.innerText = "Confirm Account";
                }}
            }});
        </script>
    </body>
    </html>
    """

