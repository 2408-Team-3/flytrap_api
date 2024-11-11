import jwt
import datetime
from flask import request
from app.config import SECRET_KEY

class TokenManager:
    def create_access_token(self, user_uuid, is_root, expires_in=20):
        return jwt.encode(
            {
                "user_uuid": user_uuid,
                "is_root": is_root,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
            },
            SECRET_KEY,
            algorithm="HS256"
        )

    def create_refresh_token(self, user_uuid, is_root, expires_in=7):
        return jwt.encode(
            {
                "user_uuid": user_uuid,
                "is_root": is_root,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=expires_in),
            },
            SECRET_KEY,
            algorithm="HS256"
        )

    def decode_token(self, token):
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    def refresh_access_token(self):
        refresh_token = request.cookies.get("refresh_token")
        print("refresh token: ", refresh_token)
        print("cookies here", request.cookies)
        if not refresh_token:
            return None, {"status": "error", "message": "No refresh token found"}
        
        try:
            payload = self.decode_token(refresh_token)
            print("refresh token payload", payload)
            new_access_token = self.create_access_token(
                payload["user_uuid"], payload.get("is_root")
            )
            return new_access_token, None
        except jwt.ExpiredSignatureError:
            return None, {"status": "error", "message": "Token expired"}
        except jwt.InvalidTokenError:
            return None, {"status": "error", "message": "Invalid token"}