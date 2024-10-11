from fastapi import Depends, Request

async def get_current_user_authorization(request: Request):
    print("****************** This is a dynamically imported module function")
    return True
