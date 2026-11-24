import os, sqlite3, secrets
from pathlib import Path
from flask import Flask, request, session, redirect, render_template, abort
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
root=Path(app.instance_path); root.mkdir(exist_ok=True)
key=root/'secret'
if not key.exists(): key.write_bytes(secrets.token_bytes(32))
app.secret_key=key.read_bytes(); app.config.update(MAX_CONTENT_LENGTH=32768,SESSION_COOKIE_SAMESITE='Lax')
# Embedded HTTPS previews need a cross-site cookie; keep local HTTP unchanged.
if os.environ.get('HUBSOC_PREVIEW') == '1':
 app.config.update(SESSION_COOKIE_SAMESITE='None', SESSION_COOKIE_SECURE=True,
                   SESSION_COOKIE_PARTITIONED=True)
from itsdangerous import URLSafeTimedSerializer, BadSignature
preview = os.environ.get('HUBSOC_PREVIEW') == '1'
preview_signer = URLSafeTimedSerializer(app.secret_key, salt='preview-tab-v1')
@app.after_request
def private_response(response):
 if request.path == '/': response.headers['Cache-Control'] = 'no-store'
 return response

def db():
 c=sqlite3.connect(root/'hub.db'); c.row_factory=sqlite3.Row; return c
with db() as c:
 c.executescript('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT UNIQUE,pw TEXT); CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY,author TEXT,body TEXT,topic TEXT,stamp TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS likes(post INTEGER,user TEXT,PRIMARY KEY(post,user));')
 if not c.execute('select 1 from posts').fetchone(): c.execute('insert into posts(author,body,topic) values(?,?,?)',('hubsoc','Добро пожаловать в hubsoc! Здесь можно делиться находками, показывать свои работы и искать единомышленников. Чем вы увлечены сейчас?','Общение'))
topics=['Общение','Дизайн','Музыка','Технологии']
@app.route('/',methods=['GET','POST'])
def home():
 state=session
 if preview:
  state={}
  supplied=request.headers.get('X-Hubsoc-Session')
  if supplied:
   try: state=preview_signer.loads(supplied,max_age=43200)
   except BadSignature: pass
 token=state.setdefault('csrf',secrets.token_hex(24)); user=state.get('user'); error=''; topic=request.args.get('topic',''); q=request.args.get('q','')[:100]
 with db() as c:
  if request.method=='POST':
   f=request.form; a=f.get('action'); name=f.get('name','').strip(); pw=f.get('pw',''); body=f.get('body','').strip()
   if f.get('csrf')!=token:
    return render_template('expired.html'), 403
   if a in ('login','register'):
    if a=='register':
     if not (2<=len(name)<=32 and name.casefold()!='hubsoc' and 8<=len(pw)<=200): error='Имя: 2–32 символа, пароль: 8–200. Имя hubsoc зарезервировано.'
     else:
      try: c.execute('insert into users(name,pw) values(?,?)',(name,generate_password_hash(pw)))
      except sqlite3.IntegrityError: error='Это имя уже занято.'
    row=c.execute('select pw from users where name=?',(name,)).fetchone()
    if not error:
     if row and check_password_hash(row[0],pw): state.clear(); state['user']=name
     else: error='Неверное имя или пароль.'
   elif a=='logout': state.clear()
   elif not user: abort(403)
   elif a=='post' and 0<len(body)<=1500 and f.get('topic') in topics: c.execute('insert into posts(author,body,topic) values(?,?,?)',(user,body,f['topic']))
   elif a=='like':
    pid=f.get('id'); row=c.execute('select id from posts where id=?',(pid,)).fetchone()
    if not row: abort(404)
    if not c.execute('delete from likes where post=? and user=?',(pid,user)).rowcount: c.execute('insert into likes values(?,?)',(pid,user))
   else: abort(400)
   if not error:
    destination=request.full_path if a=='like' else '/'
    if not preview: return redirect(destination)
    state.setdefault('csrf',secrets.token_hex(24))
    return {'destination':destination,'ticket':preview_signer.dumps(state)}
  posts=c.execute("select p.*, (select count(*) from likes where post=p.id) n,(select count(*) from likes where post=p.id and user=?) liked from posts p where (?='' or topic=?) and instr(lower(body||author),lower(?))>0 order by id desc limit 100",(user,topic,topic,q)).fetchall()
 ticket=preview_signer.dumps(state) if preview else ''
 return render_template('index.html',**locals())
