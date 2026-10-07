import hashlib
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import mysql.connector

from app.database import get_db_connection


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str
class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

def hash_password(password: str) -> str:
    """
    Creates a secure salted password hash.

    The stored format is:
    salt_hex$hash_hex
    """

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )

    return f"{salt.hex()}${password_hash.hex()}"
def verify_password(password: str, stored_password_hash: str) -> bool:
    """
    Verifies a password against the stored salted PBKDF2 hash.
    """

    try:
        salt_hex, hash_hex = stored_password_hash.split("$", 1)

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000,
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash,
        )

    except (ValueError, TypeError):
        return False

@router.post("/register")
def register_user(data: RegisterRequest):

    connection = None
    cursor = None

    allowed_roles = {
        "lawyer",
        "associate",
        "client",
    }

    # Clean input
    name = data.name.strip()
    email = data.email.strip().lower()
    role_name = data.role.strip().lower()

    # Validate role
    if role_name not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Choose lawyer, associate, or client.",
        )

    # Basic email validation
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address.",
        )

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check whether email already exists
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (email,),
        )

        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email is already registered.",
            )

        # Find role ID
        cursor.execute(
            """
            SELECT id
            FROM roles
            WHERE role_name = %s
            """,
            (role_name,),
        )

        role = cursor.fetchone()

        if role is None:
            raise HTTPException(
                status_code=400,
                detail="Role does not exist in database.",
            )

        # Hash password
        password_hash = hash_password(data.password)

        # Insert user
        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                role_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                email,
                password_hash,
                role["id"],
            ),
        )

        connection.commit()

        return {
            "status": "success",
            "message": "User registered successfully.",
            "user": {
                "id": cursor.lastrowid,
                "name": name,
                "email": email,
                "role": role_name,
            },
        }

    except HTTPException:
        raise

    except mysql.connector.Error as exc:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(exc)}",
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
