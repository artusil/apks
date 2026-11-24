let detachFeed=()=>{}, audible=false;
let owner=null, userPaused=null;
function resumeVisible(){
 const reel=activeReel(),v=reel?.querySelector('video');
 if(!v || v===userPaused || !v.paused || v.error || reel.dataset.player==='blocked')return;
 playOnly(v);
}
function silence(v){v.muted=true;v.pause();if(owner===v)owner=null}
function stopFeed(){if(owner)silence(owner);document.querySelectorAll('.reel video').forEach(silence)}
let attempt=0;
async function playOnly(v){
 const eligible=()=>v?.isConnected && v.closest('.reel')===activeReel() && !document.hidden && !document.querySelector('dialog[open]');
 if(!eligible())return;
 const reel=v.closest('.reel');delete reel.dataset.player;
 const seq=++attempt;
 if(owner && owner!==v)silence(owner);
 owner=v;v.muted=!audible;
 try{await v.play();return}catch(error){
  if(seq!==attempt || owner!==v || !eligible())return;
  // Some embedded browsers grant audible playback separately for each element.
  if(error.name==='NotAllowedError' && !v.muted){
   audible=false;document.querySelectorAll('.reel').forEach(syncSound);
   try{await v.play();return}catch{/* Leave the manual play control visible. */}
  }
  if(seq===attempt && owner===v && v.paused){silence(v);reel.dataset.player=v.error?'error':'blocked';reel.classList.add('paused')}
 }
}
function toggle(v){
 if(v.paused||v.error){userPaused=null;if(v.error)v.load();playOnly(v)}
 else{userPaused=v;silence(v)}
}
function activeReel(root=document.querySelector('.reels')) {
 if (!root || !root.clientHeight) return null;
 const reel=root.children[Math.round(root.scrollTop/root.clientHeight)];
 return reel?.classList.contains('reel') ? reel : null;
}
function step(reel,n,wrap=false){
 const root=reel.parentElement, clips=[...root.children], index=clips.indexOf(reel)+n;
 const target=wrap ? (index+clips.length)%clips.length : Math.max(0,Math.min(clips.length-1,index));
 root.scrollTo({top:target*root.clientHeight,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
}
// A trackpad gesture can dispatch dozens of wheel events (including momentum).
// Treat it as one page turn, without hijacking search, dialogs or the sidebar.
let wheelAt=-Infinity,wheelTotal=0,wheelDone=false;
document.addEventListener('wheel',e=>{
 if(!matchMedia('(min-width:741px)').matches || e.ctrlKey || Math.abs(e.deltaX)>Math.abs(e.deltaY)
   || !e.target.closest('.theater') || e.target.closest('.station,input,textarea,select') || document.querySelector('dialog[open]')) return;
 const reel=activeReel();if(!reel || !e.deltaY)return;
 e.preventDefault();const now=performance.now();
 if(now-wheelAt>160 || Math.sign(e.deltaY)!==Math.sign(wheelTotal)){wheelTotal=0;wheelDone=false}
 wheelAt=now;wheelTotal+=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?reel.clientHeight:1);
 if(!wheelDone && Math.abs(wheelTotal)>=20){wheelDone=true;step(reel,Math.sign(wheelTotal))}
},{passive:false});
function watchClips(event){
 detachFeed();stopFeed();
 const root=document.querySelector('.reels');if(!root)return;
 const hash=document.getElementById(location.hash.slice(1));if(event?.type!=='visibilitychange' && hash?.classList.contains('reel'))root.scrollTop=hash.offsetTop-root.firstElementChild.offsetTop;
 let current=null,frame=0,settleTimer;
 function update(){
  frame=0;const next=activeReel(root);
  if(next===current)return;current=next;userPaused=null;
  stopFeed();if(!next)return;
  playOnly(next.querySelector('video'));
  const upcoming=next.nextElementSibling?.querySelector('video');if(upcoming?.preload==='none')upcoming.preload='auto';
 }
 function schedule(){
  if(!frame)frame=requestAnimationFrame(update);
  clearTimeout(settleTimer);settleTimer=setTimeout(()=>{update();resumeVisible()},180);
 }
 for(const reel of root.querySelectorAll('.reel')){
  const v=reel.querySelector('video');syncSound(reel);v.onerror=()=>{reel.dataset.player='error'};v.onplaying=()=>{delete reel.dataset.player};v.onpause=()=>reel.classList.add('paused');v.onplay=()=>reel.classList.remove('paused');initTransport(reel,v);
 }
 root.addEventListener('scroll',schedule,{passive:true});root.addEventListener('scrollend',schedule);
 window.addEventListener('resize',schedule);
 detachFeed=()=>{clearTimeout(settleTimer);cancelAnimationFrame(frame);root.removeEventListener('scroll',schedule);root.removeEventListener('scrollend',schedule);window.removeEventListener('resize',schedule)};
 update();
}
document.addEventListener('click',e=>{const btn=e.target.closest('[data-act]');if(!btn)return;const r=btn.closest('.reel'),v=r.querySelector('video');if(btn.dataset.act==='play')handleTap(r,v,e.detail);if(btn.dataset.act==='next')step(r,1);if(btn.dataset.act==='sound'){audible=!audible;document.querySelectorAll('.reel').forEach(syncSound);if(audible)playOnly(v)}});
function syncSound(reel){const v=reel.querySelector('video'),b=reel.querySelector('[data-act=sound]');v.muted=v!==owner||!audible;b.textContent=audible?'🔊':'🔇';b.title=audible?'Выключить звук':'Включить звук';b.setAttribute('aria-label',b.title);b.setAttribute('aria-pressed',String(audible))}

document.addEventListener('keydown',e=>{
 if(e.altKey||e.metaKey||e.ctrlKey||document.querySelector('dialog[open]')||e.target.closest('input,textarea,select,[contenteditable=true]'))return;
 const reel=activeReel();if(!reel)return;
 if(['ArrowDown','PageDown','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();if(!e.repeat)step(reel,['ArrowDown','PageDown'].includes(e.key)?1:-1)}
 else if(e.key===' '&&!e.target.closest('button,a')){e.preventDefault();toggle(reel.querySelector('video'))}
});
document.addEventListener('DOMContentLoaded',watchClips);document.addEventListener('hubsoc:render',watchClips);document.addEventListener('visibilitychange',()=>{if(document.hidden)stopFeed();else resumeVisible()});
document.addEventListener('click',async e=>{
 const opener=e.target.closest('[data-comments]');if(!opener)return;
 const dialog=document.querySelector('#discussion'),thread=dialog.querySelector('#thread'),pid=opener.dataset.comments;
 const field=dialog.querySelector('[name=id]');if(field)field.value=pid;
 const vid=opener.closest('.reel').querySelector('video'),playing=!vid.paused;vid.pause();
 dialog.addEventListener('close',()=>{if(playing&&!document.hidden&&!document.querySelector('dialog[open]'))playOnly(vid)},{once:true});
 dialog.dataset.post=pid;thread.textContent='Загрузка…';dialog.showModal();
 try{const res=await fetch('/comments/'+pid);if(!res.ok)throw Error();const {items}=await res.json();if(dialog.dataset.post!==pid)return;
 thread.textContent=items.length?'':'Пока тихо. Оставь первый комментарий.';
 for(const item of items){const row=document.createElement('div'),name=document.createElement('strong'),body=document.createElement('p');row.className='reply';name.textContent='@'+item.user;body.textContent=item.body;row.append(name,body);thread.append(row)}
 }catch{if(dialog.dataset.post===pid)thread.textContent='Не удалось загрузить обсуждение.'}
});
let tapTimer,previousTap;
function handleTap(r,v,detail){if(v.paused||v.error){clearTimeout(tapTimer);tapTimer=null;toggle(v);return}if(detail===0){toggle(v);return}if(tapTimer&&previousTap===r){clearTimeout(tapTimer);tapTimer=null;const like=r.querySelector('[aria-label="Нравится"]');const heart=document.createElement('b');heart.className='burst';heart.textContent='♥';r.append(heart);setTimeout(()=>heart.remove(),680);if(like.getAttribute('aria-pressed')!=='true')setTimeout(()=>like.click(),200);return}clearTimeout(tapTimer);previousTap=r;tapTimer=setTimeout(()=>{toggle(v);tapTimer=null},260)}
document.addEventListener('click',async e=>{const b=e.target.closest('[data-share],[data-invite]');if(!b)return;const url=new URL('/',location.href);const reel=b.closest('.reel');if(reel)url.hash=reel.id;try{if(navigator.share){await navigator.share({title:reel?'Клип в hubsoc':'Присоединяйся к hubsoc',url:url.href});return}await navigator.clipboard.writeText(url.href);const old=b.innerHTML;b.textContent='✓';setTimeout(()=>b.innerHTML=old,1500)}catch(err){if(err.name!=='AbortError')prompt('Скопируй ссылку',url.href)}});
document.addEventListener('click',e=>{const b=e.target.closest('[data-step]');if(!b)return;const root=document.querySelector('.reels');const reel=root?.children[Math.round(root.scrollTop/root.clientHeight)];if(reel?.classList.contains('reel'))step(reel,Number(b.dataset.step))});
// Playback preferences are local to this browser and do not require an account.
const speeds=[1,1.25,1.5,2,.75];
function pref(key){try{return localStorage.getItem('hubsoc-'+key)}catch{return null}}
function setPref(key,value){try{localStorage.setItem('hubsoc-'+key,value)}catch{}}
let speed=Number(pref('speed'));if(!speeds.includes(speed))speed=1;
let autoNext=pref('auto-next')==='true';
function initTransport(reel,video){
 const seek=reel.querySelector('[data-seek]'),time=reel.querySelector('output'),rate=reel.querySelector('[data-speed]');
 const prefBox=document.querySelector('[data-autonext]');if(prefBox)prefBox.checked=autoNext;
 video.loop=!autoNext;video.playbackRate=speed;rate.textContent=`${speed}×`;
 const sync=()=>{const t=Math.floor(video.currentTime||0);time.value=`${Math.floor(t/60)}:${String(t%60).padStart(2,'0')}`;seek.value=video.duration?1000*video.currentTime/video.duration:0;seek.style.setProperty('--played',seek.value/10+'%')};
 video.ontimeupdate=sync;video.onloadedmetadata=sync;seek.oninput=()=>{if(Number.isFinite(video.duration))video.currentTime=video.duration*seek.value/1000};
 video.onended=()=>{if(!autoNext||document.hidden||document.querySelector('dialog[open]'))return;if(reel.parentNode.children.length>1)step(reel,1,true);else{video.currentTime=0;playOnly(video)}};
 rate.onclick=()=>{speed=speeds[(speeds.indexOf(speed)+1)%speeds.length];setPref('speed',speed);document.querySelectorAll('.reel').forEach(r=>{r.querySelector('video').playbackRate=speed;r.querySelector('[data-speed]').textContent=speed+'×'})};
}
document.addEventListener('change',e=>{if(!e.target.matches('[data-autonext]'))return;autoNext=e.target.checked;setPref('auto-next',autoNext);document.querySelectorAll('.reel video').forEach(v=>v.loop=!autoNext)});
document.addEventListener('click',e=>{
 const lib=document.querySelector('#library');if(!lib)return;
 if(e.target.closest('[data-open-library]')){
  const playing=[...document.querySelectorAll('.reel video')].find(v=>!v.paused);playing?.pause();let selected=false;
  lib.addEventListener('close',()=>{selected=lib.returnValue==='pick';if(!selected&&playing&&!document.hidden)playOnly(playing)},{once:true});lib.returnValue='';lib.showModal();lib.querySelector('input').focus();
 }else if(e.target.closest('[data-close-library]'))lib.close();
 else if(e.target.closest('[data-pick]')){const reel=document.getElementById(e.target.closest('[data-pick]').dataset.pick);lib.close('pick');reel.scrollIntoView({block:'nearest'});playOnly(reel.querySelector('video'));}
});
document.addEventListener('input',e=>{if(!e.target.matches('[data-find-clip]'))return;const query=e.target.value.toLocaleLowerCase('ru').trim();let hits=0;document.querySelectorAll('[data-pick]').forEach(b=>{b.hidden=!b.textContent.toLocaleLowerCase('ru').includes(query);if(!b.hidden)hits++});document.querySelector('[data-no-results]').hidden=hits!==0});

// Delegate dialog controls: preview navigation replaces the body without reloading JS.
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-open],[data-close]');if(!button)return;
 if(button.dataset.close)document.getElementById(button.dataset.close)?.close();
 if(button.dataset.open){const dialog=document.getElementById(button.dataset.open);if(dialog&&!dialog.open)dialog.showModal()}
});

document.addEventListener('close',resumeVisible,true);
window.addEventListener('pageshow',e=>{if(e.persisted)resumeVisible()});
window.addEventListener('pagehide',stopFeed);
document.addEventListener('hubsoc:before-render',stopFeed);
let draftUrl;
document.addEventListener('change',e=>{
 const input=e.target;if(!input.matches('#upload input[type=file]'))return;
 const d=input.closest('dialog'),v=d.querySelector('[data-draft]'),status=d.querySelector('[data-upload-status]');
 if(draftUrl)URL.revokeObjectURL(draftUrl);draftUrl=null;v.removeAttribute('src');v.hidden=true;d.querySelector('[data-placeholder]').hidden=false;
 const file=input.files[0];let error='';if(file?.size>64*1024*1024)error='Файл больше 64 МБ.';else if(file&&!/\.(mp4|webm)$/i.test(file.name)&&!['video/mp4','video/webm'].includes(file.type))error='Выбери видео MP4 или WebM.';
 input.setCustomValidity(error);status.textContent=error;if(!file||error)return;
 draftUrl=URL.createObjectURL(file);v.src=draftUrl;v.hidden=false;d.querySelector('[data-placeholder]').hidden=true;
 v.onerror=()=>{status.textContent='Этот плеер не читает файл. Для совместимости используй MP4 с видео H.264.'};
});
document.addEventListener('submit',e=>{if(e.target.closest('#upload'))e.target.querySelector('[data-upload-status]').textContent='Публикуем видео… Не закрывай окно.'});
document.addEventListener('close',e=>{if(e.target.id==='upload')e.target.querySelector('video')?.pause()},true);
document.addEventListener('click',e=>{if(e.target.closest('[data-hide-notice]'))e.target.closest('.publish-toast').remove()});
document.addEventListener('hubsoc:before-render',()=>{if(draftUrl){URL.revokeObjectURL(draftUrl);draftUrl=null}});
