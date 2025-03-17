from ninja import NinjaAPI, Schema

api = NinjaAPI()


# @api.get("/hello")
# def hello(request):
#     return "Hello world"


# @api.get("/hello")
# def hello(request, name="world"):
#     return f"Hello {name}"

class UserSchema(Schema):
    username: str
    email: str
    first_name: str
    last_name: str


class Error(Schema):
    message: str


@api.get("/me", response={200: UserSchema, 403: Error})
def me(request):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    return request.user


class HelloSchema(Schema):
    name: str = "world"


@api.post("/hello")
def hello(request, data: HelloSchema):
    return f"Hello {data.name}"


@api.get("/math")
def math(request, a: int, b: int):
    return {"add": a + b, "multiply": a * b}


@api.get("/math/{a}and{b}")
def math(request, a: int, b: int):
    return {"add": a + b, "multiply": a * b}
