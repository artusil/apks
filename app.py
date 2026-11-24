import os, sqlite3, secrets
from hashlib import sha256
from pathlib import Path
from flask import Flask, request, session, redirect, render_template, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
# Serve the base and responsive rules together. A new build gets a new path,
# so even caching preview proxies cannot mix old base CSS with new markup.
style_dir = Path(app.static_folder)
stylesheet = b'\n'.join((style_dir / name).read_bytes() for name in ('style.css', 'desktop.css'))
style_path = '/assets/hubsoc-' + sha256(stylesheet).hexdigest()[:16] + '.css'
app.jinja_env.globals.update(style_path=style_path, js_version=sha256((style_dir/'clips.js').read_bytes()).hexdigest()[:16])
@app.get(style_path)
def site_styles():
 return app.response_class(stylesheet, mimetype='text/css', headers={'Cache-Control':'public, max-age=31536000, immutable'})

root=Path(app.instance_path); root.mkdir(exist_ok=True)
key=root/'secret'
if not key.exists(): key.write_bytes(secrets.token_bytes(32))
app.secret_key=key.read_bytes(); app.config.update(MAX_CONTENT_LENGTH=65*1024*1024,SESSION_COOKIE_SAMESITE='Lax')
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
 c.executescript("""CREATE TABLE IF NOT EXISTS profiles(user TEXT PRIMARY KEY, display TEXT NOT NULL, bio TEXT NOT NULL, color TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS follows(user TEXT,author TEXT,PRIMARY KEY(user,author));
 CREATE TABLE IF NOT EXISTS bookmarks(post INTEGER,user TEXT,PRIMARY KEY(post,user));
 CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY,post INTEGER NOT NULL,user TEXT NOT NULL,body TEXT NOT NULL);
 CREATE INDEX IF NOT EXISTS comments_post ON comments(post,id);
 CREATE TABLE IF NOT EXISTS clips(post INTEGER PRIMARY KEY, file TEXT NOT NULL UNIQUE);""")
 if not c.execute("select 1 from clips where file='orbit.mp4'").fetchone():
  pid=c.execute('insert into posts(author,body,topic) values(?,?,?)',('hubsoc','Погружение во фрактал · визуальный этюд','Клипы')).lastrowid
  c.execute('insert into clips values(?,?)',(pid,'orbit.mp4'))
 for file,caption in [('bloom.mp4','Цветение сигнала · генеративная графика'),('dunes.mp4','Солнечный дрейф · волны цифровой пустыни')]:
  if not c.execute('select 1 from clips where file=?',(file,)).fetchone():
   pid=c.execute('insert into posts(author,body,topic) values(?,?,?)',('hubsoc',caption,'Клипы')).lastrowid
   c.execute('insert into clips values(?,?)',(pid,file))
uploads=root/'clips'; uploads.mkdir(exist_ok=True)
colors=['#def39a','#ebe9ff','#ffceb6','#a8e1ed']
@app.get('/media/<name>')
def media(name):
 response=send_from_directory(uploads,name,conditional=True)
 response.headers['X-Content-Type-Options']='nosniff'
 return response
@app.get('/comments/<int:pid>')
def comments(pid):
 with db() as c:
  if not c.execute('select 1 from clips where post=?',(pid,)).fetchone(): abort(404)
  rows=c.execute('select user,body from comments where post=? order by id desc limit 100',(pid,)).fetchall()
 return {'items':[dict(r) for r in rows]}
@app.errorhandler(413)
def too_large(error):
 return 'Видео слишком большое. Максимум — 64 МБ.',413
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
   elif a=='profile':
    display=f.get('display','').strip(); bio=f.get('bio','').strip(); color=f.get('color','')
    if not 1<=len(display)<=32 or len(bio)>200 or color not in colors: abort(400)
    c.execute('insert or replace into profiles values(?,?,?,?)',(user,display,bio,color))
   elif a=='clip':
    video=request.files.get('video')
    if not video or len(body)>240: abort(400)
    sig=video.stream.read(12); size=video.stream.seek(0,2); video.stream.seek(0)
    ext='mp4' if sig[4:8]==b'ftyp' else 'webm' if sig[:4]==bytes.fromhex('1a45dfa3') else None
    if size>64*1024*1024: abort(413)
    if not ext: return 'Выберите видео в формате MP4 или WebM.',400
    filename=secrets.token_hex(20)+'.'+ext
    pid=c.execute('insert into posts(author,body,topic) values(?,?,?)',(user,body,'Клипы')).lastrowid
    c.execute('insert into clips values(?,?)',(pid,filename)); video.save(uploads/filename)
   elif a=='post' and 0<len(body)<=1500 and f.get('topic') in topics: c.execute('insert into posts(author,body,topic) values(?,?,?)',(user,body,f['topic']))
   elif a=='follow':
    pid=f.get('id',type=int); author=c.execute('select author from posts join clips on clips.post=posts.id where id=?',(pid,)).fetchone()
    if not author or author[0]==user: abort(400)
    if not c.execute('delete from follows where user=? and author=?',(user,author[0])).rowcount:
     c.execute('insert into follows values(?,?)',(user,author[0]))
   elif a in ('save','comment'):
    pid=f.get('id',type=int)
    if not c.execute('select 1 from clips where post=?',(pid,)).fetchone(): abort(404)
    if a=='comment':
     if not 0<len(body)<=400: abort(400)
     c.execute('insert into comments(post,user,body) values(?,?,?)',(pid,user,body))
    elif not c.execute('delete from bookmarks where post=? and user=?',(pid,user)).rowcount:
     c.execute('insert into bookmarks values(?,?)',(pid,user))
   elif a=='like':
    pid=f.get('id'); row=c.execute('select id from posts where id=?',(pid,)).fetchone()
    if not row: abort(404)
    if not c.execute('delete from likes where post=? and user=?',(pid,user)).rowcount: c.execute('insert into likes values(?,?)',(pid,user))
   else: abort(400)
   if not error:
    destination=request.full_path if a in ('like','profile','clip','login','register') else '/'
    if a in ('save','comment','follow'): destination=request.full_path+f'#clip-{pid}'
    if a=='clip': destination=f'/?published={pid}#clip-{pid}'
    if a=='post': destination='/?view=feed'
    if a=='like': destination+=f'#clip-{row[0]}'
    if not preview: return redirect(destination)
    state.setdefault('csrf',secrets.token_hex(24))
    return {'destination':destination,'ticket':preview_signer.dumps(state)}
  view=request.args.get('view','clips'); profile=c.execute('select * from profiles where user=?',(user,)).fetchone()
  saved=request.args.get('saved')=='1' and view=='clips'
  following=request.args.get('channel')=='following' and view=='clips'
  posts=c.execute("select p.*,pr.display,pr.bio,pr.color,v.file,exists(select 1 from follows where user=? and author=p.author) subscribed, exists(select 1 from bookmarks where post=p.id and user=?) marked,(select count(*) from comments where post=p.id) replies, (select count(*) from likes where post=p.id) n,(select count(*) from likes where post=p.id and user=?) liked from posts p left join profiles pr on pr.user=p.author left join clips v on v.post=p.id where (not ? or exists(select 1 from follows where user=? and author=p.author)) and (not ? or exists(select 1 from bookmarks where post=p.id and user=?)) and ((v.post is not null)=?) and (?='' or topic=?) and instr(lower(body||author),lower(?))>0 order by id desc limit 100",(user,user,user,following,user,saved,user,int(view=='clips'),topic,topic,q)).fetchall()
 ticket=preview_signer.dumps(state) if preview else ''
 return render_template('index.html',**locals())
