import requests,time,logging,random
from datetime import datetime
TELEGRAM_TOKEN="8690691652:AAETgCjYXYoY55VO9KVY8y-ISIRiAeU-_jc"
TELEGRAM_CHAT_ID="-1003742204870"
MIN_SCORE=40;MIN_TQI=0.35;BASE_MULT=2.0;SL_MULT=1.5
TP1_R=1.0;TP2_R=2.0;TP3_R=3.0
SYMBOLS=["2223","2170","2130","8230","2250","4146","2200","2070","6019","2222","1320","4325","2370","1810","1321","8030","1830","4300","2320","2190","1833","4090","2350","8010","4020","2083","4100","4220","4007","1120","1111","2081","2330","4322","4162","4194","7211","4050","2080","1831","2240","2150","4326","4260","4051","4015","1324","4292","8313","1835","2084","4262","7202","2270","1183","4006","2381","4191","4150","7203","6001","6016","1303","4170","4230","7204","4040","1834","4163","4002","1304","2290","6014","4160","2020","4261","2040","4011","1322","4145","2140","4061","6070","1323","2110","2230","1211","4142","4012","2090","2300","4161","1214","2281","2287","4291","4165","4263","2001","4323","2030","6018","2050","1302","2160","4021","4008","1301","4009","4290","1202","4327","4265","4004","7200","4071","1212","3007","2340","7040","4018","6004","4019","4147","4200","4193","4005","4240","6017","4031"]
logging.basicConfig(level=logging.INFO,format='%(asctime)s|%(message)s',datefmt='%H:%M:%S')
log=logging.getLogger(__name__)
def sd(n,d,fb=0.0): return n/d if d and d!=0 and n is not None else fb
def cl(v,lo,hi): return max(lo,min(hi,v))
def fetch_yahoo(symbol,interval="1d",range_="5d"):
 ticker=f"{symbol}.SR"
 url=f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
 headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Accept":"application/json","Accept-Language":"en-US,en;q=0.9"}
 params={"interval":interval,"range":range_,"includePrePost":"false"}
 try:
  r=requests.get(url,headers=headers,params=params,timeout=10)
  if r.status_code!=200: return None
  data=r.json()
  result=data.get("chart",{}).get("result",[])
  if not result: return None
  res=result[0]
  quotes=res.get("indicators",{}).get("quote",[{}])[0]
  timestamps=res.get("timestamps") or res.get("timestamp",[])
  closes=quotes.get("close",[]); opens=quotes.get("open",[])
  highs=quotes.get("high",[]); lows=quotes.get("low",[])
  volumes=quotes.get("volume",[])
  valid=[(t,o,h,l,c,v) for t,o,h,l,c,v in zip(timestamps,opens,highs,lows,closes,volumes) if c is not None and o is not None]
  if len(valid)<2: return None
  bars=valid[-5:] if len(valid)>=5 else valid
  cur=bars[-1]; prev=bars[-2] if len(bars)>=2 else cur
  p2=bars[-3] if len(bars)>=3 else prev; p3=bars[-4] if len(bars)>=4 else p2
  c0=cur[4];o0=cur[1];h0=cur[2];l0=cur[3];v0=cur[5] or 0
  c1=prev[4];h1=prev[2];l1=prev[3];v1=prev[5] or 0
  c2=p2[4]; c3=p3[4]
  atr=abs(h0-l0)*1.2
  rsi=50.0
  if len(valid)>=15:
   gains=[];losses=[]
   for i in range(-14,0):
    diff=valid[i][4]-valid[i-1][4]
    if diff>0: gains.append(diff)
    else: losses.append(abs(diff))
   ag=sum(gains)/14 if gains else 0; al=sum(losses)/14 if losses else 0
   if al>0: rs=ag/al; rsi=100-100/(1+rs)
   elif ag>0: rsi=100
  change=sd(c0-c1,c1,0)*100
  return {"close":c0,"open":o0,"high":h0,"low":l0,"volume":v0,"change":change,"atr":atr,"rsi":rsi,"ema20":None,"ema50":None,"recommend":None,"close1":c1,"close2":c2,"close3":c3,"high1":h1,"low1":l1,"vol1":v1,"vol2":None}
 except Exception as e: log.debug(f"Yahoo {symbol}: {e}"); return None
def fetch_all(tf="D"):
 interval="1d" if tf=="D" else "15m"; range_="5d" if tf=="D" else "1d"
 result={}
 for i in range(0,len(SYMBOLS),10):
  batch=SYMBOLS[i:i+10]
  for sym in batch:
   d=fetch_yahoo(sym,interval,range_)
   if d: result[sym]=d
  time.sleep(random.uniform(0.5,1.5))
 log.info(f"✅ Yahoo: {len(result)} سهم")
 return result
def tqi(d,er,atr,ab):
 te=cl(er,0,1); vr=sd(atr,ab,1); tv=cl((vr-0.5)/1.5,0,1)
 c=d["close"] or 0; h=d["high"] or c; l=d["low"] or c
 ts=cl(abs(sd(c-l,h-l,0.5)-0.5)*2,0,1)
 cs=[d.get("close3"),d.get("close2"),d.get("close1"),c]; cs=[x for x in cs if x is not None]
 if len(cs)>=2:
  u=sum(1 for i in range(1,len(cs)) if cs[i]>cs[i-1]); dn=sum(1 for i in range(1,len(cs)) if cs[i]<cs[i-1])
  n=len(cs)-1; ch=cs[-1]-cs[0]; tm=(u/n) if ch>0 else (dn/n) if ch<0 else 0.0
 else: tm=0.5
 return cl(te*0.35+tv*0.20+ts*0.25+tm*0.20,0,1)
def calc_er(d):
 cs=[d.get("close3"),d.get("close2"),d.get("close1"),d.get("close")]; cs=[c for c in cs if c is not None]
 if len(cs)<2: return 0.3
 return cl(sd(abs(cs[-1]-cs[0]),sum(abs(cs[i]-cs[i-1]) for i in range(1,len(cs))),0.3),0,1)
def calc_score(d,ib,e,atr,rsi):
 if not atr or atr==0: return 0.0
 c=d["close"] or 0; c3=d.get("close3") or c; h1=d.get("high1") or d.get("high") or c; l1=d.get("low1") or d.get("low") or c; v=d.get("volume") or 0; v1=d.get("vol1") or v
 dm=(c-c3) if ib else (c3-c); ms=cl(sd(dm/atr-0.3,1.7)*17,0,17); es=cl(sd(e-0.15,0.55)*17,0,17)
 vr=sd(v,v1,1) if v1 else 1; vs=cl(sd(vr-1,2)*17,0,17) if v>0 else 12
 rd=max(0,30-min(rsi,30)) if ib else max(0,max(rsi,70)-70); rs=cl(sd(rd,15)*17,0,17)
 pd=abs(c-(l1 if ib else h1)); ss=cl(16-sd(pd,atr)*10,6,16)
 return cl(ms+es+vs+rs+ss+8,0,100)
def detect(d):
 c=d.get("close")
 if not c or c<=0: return None
 atr=d.get("atr") or ((d.get("high",c)-d.get("low",c))*1.5) or c*0.02; atr=max(atr,c*0.001)
 e=calc_er(d); ae=atr*(0.5+0.5*e); tq=tqi(d,e,ae,atr); rsi=d.get("rsi") or 50
 c1=d.get("close1") or c; rec=d.get("recommend") or 0
 up=c>c-BASE_MULT*ae
 ib=up and rec>-0.5; isl=not up and rec<0.5
 if not ib and not isl: return None
 sc=calc_score(d,ib,e,ae,rsi)
 if sc<MIN_SCORE and tq<MIN_TQI: return None
 risk=ae*SL_MULT
 if ib: sl=c-risk;t1=c+risk*TP1_R;t2=c+risk*TP2_R;t3=c+risk*TP3_R
 else: sl=c+risk;t1=c-risk*TP1_R;t2=c-risk*TP2_R;t3=c-risk*TP3_R
 g="A+⭐⭐⭐" if(sc>=80 or tq>=0.70) else "A⭐⭐" if(sc>=60 or tq>=0.50) else "B⭐"
 return {"ib":ib,"c":c,"sl":sl,"t1":t1,"t2":t2,"t3":t3,"sc":sc,"tq":tq,"rsi":rsi,"g":g,"ch":d.get("change") or 0}
def send_tg(msg):
 try:
  r=requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",json={"chat_id":TELEGRAM_CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=15)
  return r.status_code==200
 except: return False
def fmt(sigs,lbl,now):
 buys=sorted([s for s in sigs if s["sig"]["ib"]],key=lambda x:x["sig"]["sc"],reverse=True)
 sells=sorted([s for s in sigs if not s["sig"]["ib"]],key=lambda x:x["sig"]["sc"],reverse=True)
 msg=f"🔍 <b>SATS|{lbl}</b>\n⏰{now}\n━━━━━━━━━━━━━━━━\n\n"
 if buys:
  msg+=f"📈<b>شراء({len(buys)})</b>\n\n"
  for x in buys:
   s=x["sig"]; e="▲" if s["ch"]>0 else "▼"
   msg+=f"🟢<b>{x['sym']}</b>|{s['g']}\n💰{s['c']:.2f}{e}{abs(s['ch']):.1f}%\n🛑SL:{s['sl']:.2f}\n🎯TP1:{s['t1']:.2f}|TP2:{s['t2']:.2f}|TP3:{s['t3']:.2f}\n📊{s['sc']:.0f}pts|TQI:{s['tq']:.2f}|RSI:{s['rsi']:.0f}\n\n"
 if sells:
  msg+=f"📉<b>بيع({len(sells)})</b>\n\n"
  for x in sells:
   s=x["sig"]; e="▲" if s["ch"]>0 else "▼"
   msg+=f"🔴<b>{x['sym']}</b>|{s['g']}\n💰{s['c']:.2f}{e}{abs(s['ch']):.1f}%\n🛑SL:{s['sl']:.2f}\n🎯TP1:{s['t1']:.2f}|TP2:{s['t2']:.2f}|TP3:{s['t3']:.2f}\n📊{s['sc']:.0f}pts|TQI:{s['tq']:.2f}|RSI:{s['rsi']:.0f}\n\n"
 msg+=f"━━━━━━━━━━━━━━━━\n📋{len(SYMBOLS)}سهم|SATSv2.0|Yahoo"
 return msg
def scan(tf):
 lbl="يومي📅" if tf=="D" else "15د⚡"; now=datetime.now().strftime("%Y-%m-%d %H:%M")
 data=fetch_all(tf)
 if not data: send_tg(f"⚠️فشل جلب البيانات({lbl})"); return
 sigs=[]
 for sym in SYMBOLS:
  d=data.get(sym)
  if not d: continue
  sig=detect(d)
  if sig: sigs.append({"sym":sym,"sig":sig})
 if sigs: send_tg(fmt(sigs,lbl,now))
 else:
  if tf=="D": send_tg(f"📋مسح يومي|{now}\n💤لا إشارات اليوم\n📊{len(data)} سهم")
def main():
 send_tg("🚀<b>SATS V2 يعمل!</b>\n📋"+str(len(SYMBOLS))+"سهم\n📡Yahoo Finance\n✅جاهز!")
 last=datetime.now().date()
 while True:
  try:
   n=datetime.now()
   if n.date()!=last and n.hour>=15 and n.minute>=30: scan("D"); last=n.date()
   mo=(n.hour==9 and n.minute>=30) or(10<=n.hour<=14) or(n.hour==15 and n.minute<=30)
   if mo: scan("15")
   time.sleep(900)
  except KeyboardInterrupt: send_tg("⛔توقف"); break
  except Exception as e: log.error(f"err:{e}"); time.sleep(60)
if __name__=="__main__": main()
