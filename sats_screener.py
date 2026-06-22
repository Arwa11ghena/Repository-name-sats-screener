import requests,time,logging,random
from datetime import datetime
TELEGRAM_TOKEN="8690691652:AAETgCjYXYoY55VO9KVY8y-ISIRiAeU-_jc"
TELEGRAM_CHAT_ID="-1003742204870"
MIN_SCORE=40;MIN_TQI=0.35;SL_MULT=1.5
TP1_R=1.0;TP2_R=2.0;TP3_R=3.0
SYMBOLS=["2223","2170","2130","8230","2250","4146","2200","2070","6019","2222","1320","4325","2370","1810","1321","8030","1830","4300","2320","2190","1833","4090","2350","8010","4020","2083","4100","4220","4007","1120","1111","2081","2330","4322","4162","4194","7211","4050","2080","1831","2240","2150","4326","4260","4051","4015","1324","4292","8313","1835","2084","4262","7202","2270","1183","4006","2381","4191","4150","7203","6001","6016","1303","4170","4230","7204","4040","1834","4163","4002","1304","2290","6014","4160","2020","4261","2040","4011","1322","4145","2140","4061","6070","1323","2110","2230","1211","4142","4012","2090","2300","4161","1214","2281","2287","4291","4165","4263","2001","4323","2030","6018","2050","1302","2160","4021","4008","1301","4009","4290","1202","4327","4265","4004","7200","4071","1212","3007","2340","7040","4018","6004","4019","4147","4200","4193","4005","4240","6017","4031"]
logging.basicConfig(level=logging.INFO,format='%(asctime)s|%(message)s',datefmt='%H:%M:%S')
log=logging.getLogger(__name__)

def send_tg(msg):
 try:
  r=requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",json={"chat_id":TELEGRAM_CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=15)
  log.info(f"TG: {r.status_code}")
  return r.status_code==200
 except Exception as e: log.error(f"TG err: {e}"); return False

def fetch_symbol(sym):
 url=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.SR"
 headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Accept":"application/json"}
 try:
  r=requests.get(url,headers=headers,params={"interval":"1d","range":"10d"},timeout=15)
  if r.status_code!=200: return None
  res=r.json().get("chart",{}).get("result",[])
  if not res: return None
  q=res[0].get("indicators",{}).get("quote",[{}])[0]
  C=q.get("close",[]); O=q.get("open",[]); H=q.get("high",[]); L=q.get("low",[]); V=q.get("volume",[])
  valid=[(o,h,l,c,v) for o,h,l,c,v in zip(O,H,L,C,V) if c and o]
  if len(valid)<4: return None
  c0,c1,c2,c3=valid[-1][3],valid[-2][3],valid[-3][3],valid[-4][3]
  h0,l0,v0=valid[-1][1],valid[-1][2],valid[-1][4] or 0
  h1,l1,v1=valid[-2][1],valid[-2][2],valid[-2][4] or 0
  atr=abs(h0-l0)*1.2 or abs(h1-l1)*1.2 or c0*0.01
  chg=(c0-c1)/c1*100 if c1 else 0
  rsi=50.0
  if len(valid)>=15:
   g=[]; ls=[]
   for i in range(-14,0):
    d=valid[i][3]-valid[i-1][3]
    if d>0: g.append(d)
    else: ls.append(abs(d))
   ag=sum(g)/14 if g else 0; al=sum(ls)/14 if ls else 0
   if al>0: rsi=100-100/(1+ag/al)
   elif ag>0: rsi=100
  return {"c":c0,"c1":c1,"c2":c2,"c3":c3,"h":h0,"l":l0,"h1":h1,"l1":l1,"v":v0,"v1":v1,"atr":atr,"rsi":rsi,"chg":chg}
 except Exception as e: log.debug(f"{sym}: {e}"); return None

def analyze(d):
 c=d["c"]; atr=d["atr"]; rsi=d["rsi"]
 if not c or c<=0 or not atr: return None
 cs=[d["c3"],d["c2"],d["c1"],c]
 direction=abs(cs[-1]-cs[0])
 volatility=sum(abs(cs[i]-cs[i-1]) for i in range(1,4))
 er=direction/volatility if volatility>0 else 0.3
 ae=atr*(0.5+0.5*er)
 ups=sum(1 for i in range(1,4) if cs[i]>cs[i-1])
 dns=sum(1 for i in range(1,4) if cs[i]<cs[i-1])
 chg=cs[-1]-cs[0]
 mom=ups/3 if chg>0 else dns/3 if chg<0 else 0
 tq=er*0.35+mom*0.45+0.20
 tq=max(0,min(1,tq))
 dm=c-d["c3"]; ms=max(0,min(17,(dm/atr-0.3)/1.7*17))
 es=max(0,min(17,(er-0.15)/0.55*17))
 vr=d["v"]/d["v1"] if d["v1"] else 1
 vs=max(0,min(17,(vr-1)/2*17)) if d["v"]>0 else 12
 rd=max(0,30-min(rsi,30)); rs=max(0,min(17,rd/15*17))
 pd=abs(c-d["l1"]); ss=max(6,min(16,16-pd/atr*10))
 sc=ms+es+vs+rs+ss+8
 if sc<MIN_SCORE and tq<MIN_TQI: return None
 risk=ae*SL_MULT
 sl=c-risk; t1=c+risk*TP1_R; t2=c+risk*TP2_R; t3=c+risk*TP3_R
 g="A+⭐⭐⭐" if sc>=80 or tq>=0.70 else "A⭐⭐" if sc>=60 or tq>=0.50 else "B⭐"
 return {"sc":sc,"tq":tq,"rsi":rsi,"sl":sl,"t1":t1,"t2":t2,"t3":t3,"g":g,"chg":d["chg"]}

def main():
 now=datetime.now().strftime("%Y-%m-%d %H:%M")
 log.info("SATS بدأ")
 send_tg(f"🔄 <b>SATS بدأ المسح</b>\n⏰{now}\n📊{len(SYMBOLS)} سهم...")
 ok=0; sigs=[]
 for i,sym in enumerate(SYMBOLS):
  d=fetch_symbol(sym)
  if d:
   ok+=1
   sig=analyze(d)
   if sig: sigs.append({"sym":sym,"sig":sig})
  if i%20==19: time.sleep(0.5)
 log.info(f"جُلب {ok} سهم | إشارات: {len(sigs)}")
 if sigs:
  sigs=sorted(sigs,key=lambda x:x["sig"]["sc"],reverse=True)
  msg=f"🔍 <b>SATS | السوق السعودي</b>\n⏰{now}\n━━━━━━━━━━━━━━━━\n\n📈 <b>إشارات ({len(sigs)})</b>\n\n"
  for x in sigs:
   s=x["sig"]; e="▲" if s["chg"]>0 else "▼"
   msg+=f"🟢 <b>{x['sym']}</b> | {s['g']}\n💰 {x['sig']['sl']+SL_MULT*0:.2f}  {e}{abs(s['chg']):.1f}%\n🛑 SL: {s['sl']:.2f}\n🎯 TP1: {s['t1']:.2f} | TP2: {s['t2']:.2f} | TP3: {s['t3']:.2f}\n📊 {s['sc']:.0f}pts | TQI: {s['tq']:.2f} | RSI: {s['rsi']:.0f}\n\n"
  msg+=f"━━━━━━━━━━━━━━━━\n📋 {ok}/{len(SYMBOLS)} سهم | SATS v2"
  send_tg(msg)
 else:
  send_tg(f"📋 <b>مسح مكتمل</b>\n⏰{now}\n💤 لا إشارات اليوم\n📊 {ok}/{len(SYMBOLS)} سهم")
 send_tg("✅ <b>SATS انتهى المسح</b>")

main()
