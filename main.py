from fastapi import FastAPI,Depends,status, Request,Form, UploadFile, File
from fastapi.responses import RedirectResponse,HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager #Loginmanager Class
from fastapi_login.exceptions import InvalidCredentialsException #Exception class
from fastapi.templating import Jinja2Templates
import os
from deta import Deta
#from deta import Drive 
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, SecretStr
from fastapi.staticfiles import StaticFiles
import datetime



app= FastAPI()

SECRET = os.urandom(24).hex()
# To obtain a suitable secret key you can run | import os; print(os.urandom(24).hex())
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


manager = LoginManager(SECRET,token_url="/auth/login",use_cookie=True)
manager.cookie_name = 'cookies'
deta = Deta()
s_db = deta.Base('student_db')


l_db = deta.Base('lecture_db')

m_db = deta.Base('message_db')

f_db = deta.Base('file_db')


#drive = deta.Drive('files')

#drive = Drive("files")

c_db = deta.Base('course_db')

#DB = {"username":{"password":"password"}} # unhashed
#teacher
teacher = LoginManager(SECRET,token_url="/auth/login/teacher",use_cookie=True)
teacher.cookie_name = 'cookies'


t_db = deta.Base('teacher_db')

upl = ['',]
trfx = ['',]

#student register
@app.get('/auth/student/register', response_class=HTMLResponse)
def create(request: Request):
    return templates.TemplateResponse('student_register.html',{'request':request})


@app.post('/student/register')
def register(request:Request,email: EmailStr = Form(...), password: str = Form(...), firstname: str = Form(...), lastname: str = Form(...), username: str = Form(...)):
    user = ({
        'email':email,
        'password':password,
        'firstname':firstname,
        'lastname':lastname,
        'username':username,
        'key':email
        })
    s_db.insert(user)
    resp = RedirectResponse(url="/student/login",status_code=status.HTTP_302_FOUND)
    return resp



###student login
@manager.user_loader
def load_user(username: str):
    """
    Get a user from the db
    :param user_id: E-Mail of the user
    :return: None or the user object
    """
    return s_db.fetch({"username?contains": username})

@app.post("/auth/login")
def login(data: OAuth2PasswordRequestForm = Depends(), email: EmailStr = Form(...)):
    username = data.username
    password = data.password
    user = load_user(username)
    pass_key = s_db.get(email)['password']
    if not user:
        raise InvalidCredentialsException
    elif password != pass_key:
        raise InvalidCredentialsException
    access_token = manager.create_access_token(
        data={"sub":username},
        expires=datetime.timedelta(hours=12)
    )
    resp = RedirectResponse(url="/student/{_}/courses",status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp,access_token)
    return resp


@app.get("/student/login",response_class=HTMLResponse)
def loginwithCreds(request:Request):
    return templates.TemplateResponse("student_login.html", {"request": request})

@app.get("/student/{_}/courses",response_class=HTMLResponse)
def Courses(request:Request,_=Depends(manager)):
    data = next(c_db.fetch())
    print(data)
    print(type(data))
    return templates.TemplateResponse("student_courselist.html", {"request": request, 'data':data})



@app.get('/student/{class_key}/dashboard')
def dash(request:Request):
    #key = list(_)[0][0]['email']
    #data = next(c_db.fetch({"email?contains" : str(key)} ))
    global upl
    global trfx
    #key = list(_)[0][0]['email']
    #data = next(c_db.fetch({"email?contains" : str(key)} ))
    url = (str(request.url)) 
    upl[0] = url
    tfx = upl[0].split('/')[-2:][0]
    trfx[0] = tfx
    l_data = l_db.get(trfx[0])
    m_data = m_db.get(trfx[0])
    f_data = f_db.get(trfx[0])
    return templates.TemplateResponse("student_dashboard.html", {"request": request,'l_data':l_data,'m_data':m_data,'f_data':f_data })
    #return {'main':'hello'}

'''
teachers registration

'''
@app.get('/auth/teacher/register', response_class=HTMLResponse)
def create(request: Request):
    return templates.TemplateResponse('teacher_register.html',{'request':request})


@app.post('/register')
def register(request:Request,email: EmailStr = Form(...), password: str = Form(...), firstname: str = Form(...), lastname: str = Form(...), username: str = Form(...)):
    user = ({
        'email':email,
        'password':password,
        'firstname':firstname,
        'lastname':lastname,
        'username':username,
        'key':email
        })
    t_db.insert(user)
    resp = RedirectResponse(url="/teacher/login",status_code=status.HTTP_302_FOUND)
    return resp

#teachers login

@teacher.user_loader
def load_user(username: str):
    """
    Get a user from the db
    :param user_id: E-Mail of the user
    :return: None or the user object
    """
    return t_db.fetch({"username?contains": username})


@app.post("/auth/login/teacher")
def login(data: OAuth2PasswordRequestForm = Depends(), email: EmailStr = Form(...)):
    username = data.username
    password = data.password
    user = load_user(username)
    pass_key = t_db.get(email)['password']
    if not user:
        raise InvalidCredentialsException
    elif password != pass_key:
        raise InvalidCredentialsException
    access_token = teacher.create_access_token(
        data={"sub":username},
         expires=datetime.timedelta(hours=12)
    )
    resp = RedirectResponse(url="/teacher/create_class",status_code=status.HTTP_302_FOUND)
    teacher.set_cookie(resp,access_token)
    return resp

@app.get("/teacher/login",response_class=HTMLResponse)
def loginwithCreds(request:Request):
    return templates.TemplateResponse("teacher_login.html", {"request": request})

@app.get("/teacher/create_class",response_class=HTMLResponse)
def Createclass(request:Request, _=Depends(teacher)):
    return templates.TemplateResponse("create_class.html", {"request": request})

@app.post('/teacher/createClass')
def Createclass(request:Request,classname:str = Form(...), classdescription : str = Form(...), email: EmailStr= Form(...)):
    import uuid
    lowercase_str = uuid.uuid4().hex 
    user = ({
        'classname':classname,
        'classdescription':classdescription,
        'class_key':lowercase_str,
        'key':lowercase_str,
        'email':email
        })
    c_db.insert(user)
    resp = RedirectResponse(url="/teacher/{_}/courses",status_code=status.HTTP_302_FOUND)
    return resp

@app.get("/teacher/{_}/courses",response_class=HTMLResponse)
def Courses(request:Request, _=Depends(teacher)):
    key = list(_)[0][0]['email']
    data = next(c_db.fetch({"email?contains" : str(key)} ))
    print(data)
    print(type(data))
    return templates.TemplateResponse("list_courses.html", {"request": request, 'data':data})


@app.get('/teacher/{class_key}/dashboard')
def dash(request:Request):
    global upl
    global trfx
    #key = list(_)[0][0]['email']
    #data = next(c_db.fetch({"email?contains" : str(key)} ))
    url = (str(request.url)) 
    upl[0] = url
    tfx = upl[0].split('/')[-2:][0]
    trfx[0] = tfx
    print(upl)
    return templates.TemplateResponse("teacher_dashboard.html", {"request": request})
    


@app.post('/teacher/class_topic')
def Courses(request:Request, lecturetitle: str = Form(...), body: str = Form(...)):
    #upl = str(request.app.url)
    user = ({
            'lecturetitle':lecturetitle,
            'body':body,
            'key': trfx[0]
            })

    

    print(user)
    #print(tfx) 
    #print(type(items))
    l_db.put(user)
    resp = RedirectResponse(url="/teacher/" + trfx[0] + "/dashboard",status_code=status.HTTP_302_FOUND)
    return resp



@app.post("/uploaddata/")
async def upload_file(request:Request,file: UploadFile = File(...)):
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api


    cloudinary.config( 
      cloud_name = "noiro", 
      api_key = "577941549789354", 
      api_secret = "4y7_LMBvR9mIIqTFQKOUUB431_g",
    )

    res = cloudinary.uploader.upload(file.file,overwrite = True,  resource_type = "auto")

    print(res)
    print(file.filename)

    user = ({
            'materialname':file.filename,
            'url':res['url'],
            'key': trfx[0]
            })
    print(user)
    #print(tfx) 
    #print(type(items))
    f_db.put(user)
    rep = RedirectResponse(url="/teacher/" + trfx[0] + "/dashboard",status_code=status.HTTP_302_FOUND)
    return rep


@app.post("/message")
async def message(request:Request,message: str = Form(...)):
    # Do here your stuff with the file
    user = ({"message": message,
            'key': trfx[0]
        })
    m_db.put(user)
    resp = RedirectResponse(url="/teacher/" + trfx[0] + "/dashboard",status_code=status.HTTP_302_FOUND)
    return resp

@app.get("/teacher/{_}/courses",response_class=HTMLResponse)
def Courses(request:Request, _=Depends(teacher)):
    key = list(_)[0][0]['email']
    data = next(c_db.fetch({"email?contains" : str(key)} ))
    print(data)
    print(type(data))
    return templates.TemplateResponse("list_courses.html", {"request": request, 'data':data})


'''
Homepge
'''
@app.get('/', response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("home.html", {"request": request})


# Using Request instance
@app.get("/url-list-from-request")
def get_all_urls_from_request(request: Request):
    url_list = [
        {"path": route.path, "name": route.name} for route in request.app.routes
    ]
    return url_list


@app.get('/admin')
def admin_section(request:Request):
    students = next(s_db.fetch())
    teachers = next(t_db.fetch())
    courses = next(c_db.fetch())
    return templates.TemplateResponse("admin.html", {"request": request, 'courses':courses, 'teachers':teachers,'students':students})


@app.post('/teach/delete')
def delete_teach(request:Request,teach: str = Form(...)):
    t_db.delete(teach)
    resp = RedirectResponse(url="/admin",status_code=status.HTTP_302_FOUND)
    return resp

@app.post('/student/delete')
def delete_teach(request:Request,student: str = Form(...)):
    s_db.delete(student)
    resp = RedirectResponse(url="/admin",status_code=status.HTTP_302_FOUND)
    return resp

@app.post('/course/delete')
def delete_teach(request:Request,course: str = Form(...)):
    c_db.delete(course)
    resp = RedirectResponse(url="/admin",status_code=status.HTTP_302_FOUND)
    return resp