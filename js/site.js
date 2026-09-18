/* Dream Girls — shared interactivity */
(function(){
  /* ── Live open status (America/Chicago), from real hours ── */
  // day: 0=Sun..6=Sat ; [open, close] in minutes; close < open means past midnight
  var HOURS = {3:[20*60,3*60],4:[20*60,3*60],5:[20*60,4*60],6:[20*60,4*60]}; // Wed,Thu,Fri,Sat
  var NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  function nowCT(){
    try{
      var p=new Intl.DateTimeFormat('en-US',{timeZone:'America/Chicago',weekday:'short',hour:'numeric',minute:'numeric',hour12:false}).formatToParts(new Date());
      var o={}; p.forEach(function(x){o[x.type]=x.value});
      return {day:NAMES.indexOf(o.weekday), min:(parseInt(o.hour,10)%24)*60+parseInt(o.minute,10)};
    }catch(e){ var d=new Date(); return {day:d.getDay(),min:d.getHours()*60+d.getMinutes()}; }
  }
  function fmt(m){ var h=Math.floor(m/60)%24, ap=h>=12?'PM':'AM'; h=h%12||12; return h+ap; }
  function status(){
    var t=nowCT(), d=t.day, m=t.min;
    // still open from yesterday's session?
    var y=(d+6)%7; if(HOURS[y] && m<HOURS[y][1]) return {open:true,text:'Open now · closes '+fmt(HOURS[y][1])};
    if(HOURS[d]){
      if(m>=HOURS[d][0]) return {open:true,text:'Open now · closes '+fmt(HOURS[d][1])};
      return {open:false,text:'Opens tonight at '+fmt(HOURS[d][0])};
    }
    for(var i=1;i<=7;i++){ var n=(d+i)%7; if(HOURS[n]) return {open:false,text:'Closed today · opens '+NAMES[n]+' '+fmt(HOURS[n][0])}; }
    return {open:false,text:'See hours'};
  }
  function paint(){
    var s=status();
    document.querySelectorAll('[data-status]').forEach(function(el){
      el.classList.toggle('closed',!s.open); var t=el.querySelector('span'); if(t) t.textContent=s.text;
    });
  }
  paint(); setInterval(paint,60000);

  /* ── Scroll reveal (one pass, IntersectionObserver) ── */
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target);}})},{threshold:.12,rootMargin:'0px 0px -40px 0px'});
    document.querySelectorAll('.rv').forEach(function(el){io.observe(el)});
  } else { document.querySelectorAll('.rv').forEach(function(el){el.classList.add('on')}); }

  /* ── Floating mobile CTA ── */
  if(!document.querySelector('.fab')){
    var f=document.createElement('div'); f.className='fab';
    f.innerHTML='<a class="btn btn-primary" href="contact.html#party">Book a party</a><a class="btn btn-dark" href="tel:+16123337326" aria-label="Call">Call</a>';
    document.body.appendChild(f);
  }
})();
