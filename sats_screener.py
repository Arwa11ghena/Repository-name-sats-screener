import requests,time,logging
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
COLS=["name","close","open","high","low","volume","change","ATR","RSI","EMA20","EMA50","Recommend.All","close[1]","close[2]","close[3]","high[1]","low[1]","volume[1]","volume[2]"]
COLS15=["name","close|15","open|15","high|15","low|15","volume|15","change|15","ATR|15","RSI|15","EMA20|15","EMA50|15","Recommend.All|15","close[1]|15","close[2]|15","close[3]|15","high[1]|15","low[1]|15","volume[1]|15","volume[2]|15"]
def fetch(tf="D"):
 tickers=[f"TADAWUL:{s}" for s in SYMBOLS]
 cols=COLS15 if tf=="15" else COLS
 payload={"filter":[],"symbols":{"tickers":tickers,"query":{"types":[]}},"columns":cols,"range":[0,len(SYMBOLS)]}
 headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0","Origin":"https://www.tradingview.com","Referer":"https://www.tradingview.com/"}
 try:
  r=requests.post("https://scanner.tradingview.com/saudi/scan",json=payload,headers=headers,timeout=30)
  if r.status_code!=200: return {}
  res={}
  for item in r.json().get("data",[]):
   sym=item["s"].replace("TADAWUL:",""); vals=item.get("d",[])
   if len(vals)<7: continue
   res[sym]={"close":vals[1],"open":vals[2],"high":vals[3],"low":vals[4],"volume":vals[5],"change":vals[6],"atr":vals[7] if len(vals)>7 else None,"rsi":vals[8] if len(vals)>8 else 50.0,"ema20":vals[9] if len(vals)>9 else None,"ema50":vals[10] if len(vals)>10 else None,"recommend":vals[11] if len(vals)>11 else None,"close1":vals[12] if len(vals)>12 else None,"close2":vals[13] if len(vals)>13 else None,"close3":vals[14] if len(vals)>14 else None,"high1":vals[15] if len(vals)>15 else None,"low1":vals[16] if len(vals)>16 else None,"vol1":vals[17] if len(vals)>17 else None}
  return res
 except Exception as e: log.error(f"err:{e}"); return {}
def tqi(d,er,atr,ab):
 te=cl(er,0,1); vr=sd(atr,ab,1); tv=cl((vr-0.5)/1.5,0,1)
 c=d["close"] or 0; h=d["high"] or c; l=d["low"] or c
 ts=cl(abs(sd(c-l,h-l,0.5)-0.5)*2,0,1)
 cs=[d.get("close3"),d.get("close2"),d.get("close1"),c]; cs=[x for x in cs if x]
 if len(cs)>=2:
  u=sum(1 for i in range(1,len(cs)) if cs[i]>cs[i-1]); dn=sum(1 for i in range(1,len(cs)) if cs[i]<cs[i-1]); n=len(cs)-1; ch=cs[-1]-cs[0]
  tm=(u/n) if ch>0 else (dn/n) if ch<0 else 0.0
 else: tm=0.5
 return cl(te*0.35+tv*0.20+ts*0.25+tm*0.20,0,1)
def er(d):
 cs=[d.get("close3"),d.get("close2"),d.get("close1"),d.get("close")]; cs=[c for c in cs if c]
 if len(cs)<2: return 0.3
 return cl(sd(abs(cs[-1]-cs[0]),sum(abs(cs[i]-cs[i-1]) for i in range(1,len(cs))),0.3),0,1)
def score(d,ib,e,atr,rsi):
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
 e=er(d); ae=atr*(0.5+0.5*e); tq=tqi(d,e,ae,atr); rsi=d.get("rsi") or 50
 c1=d.get("close1") or c; em20=d.get("ema20"); em50=d.get("ema50"); rec=d.get("recommend") or 0
 up=c>c-BASE_MULT*ae
 if em20 and em50: up=up and em20>em50
 ib=up and (c1<=c1+BASE_MULT*ae or rec>0.3); isl=not up and (c1>=c1-BASE_MULT*ae or rec<-0.3)
 if not ib and not isl: return None
 sc=score(d,ib,e,ae,rsi)
 if sc<MIN_SCORE and tq<MIN_TQI: return None
 risk=ae*SL_MULT
 if ib: sl=c-risk;t1=c+risk*TP1_R;t2=c+risk*TP2_R;t3=c+risk*TP3_R
 else: sl=c+risk;t1=c-risk*TP1_R;t2=c-risk*TP2_R;t3=c-risk*TP3_R
 g="A+⭐⭐⭐" if(sc>=80 or tq>=0.70) else "A⭐⭐" if(sc>=60 or tq>=0.50) else "B⭐"
 return {"ib":ib,"c":c,"sl":sl,"t1":t1,"t2":t2,"t3":t3,"sc":sc,"tq":tq,"rsi":rsi,"g":g,"ch":d.get("change") or 0}
def tg(msg):
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
 msg+=f"━━━━━━━━━━━━━━━━\n📋{len(SYMBOLS)}سهم|SATSv1.12"
 return msg
def scan(tf):
 lbl="يومي📅" if tf=="D" else "15د⚡"; now=datetime.now().strftime("%Y-%m-%d %H:%M")
 data=fetch(tf)
 if not data: tg(f"⚠️فشل جلب البيانات({lbl})"); return
 sigs=[]
 for sym in SYMBOLS:
  d=data.get(sym)
  if not d: continue
  sig=detect(d)
  if sig: sigs.append({"sym":sym,"sig":sig})
 if sigs: tg(fmt(sigs,lbl,now))
 else:
  if tf=="D": tg(f"📋مسح يومي|{now}\n💤لا إشارات اليوم\n📊{len(data)}سهم")
def main():
 tg("🚀<b>SATS Screener يعمل!</b>\n📋"+str(len(SYMBOLS))+"سهم\n✅جاهز للإشارات!")
 last=datetime.now().date()
 while True:
  try:
   n=datetime.now()
   if n.date()!=last and n.hour>=15 and n.minute>=30: scan("D"); last=n.date()
   mo=(n.hour==9 and n.minute>=30) or(10<=n.hour<=14) or(n.hour==15 and n.minute<=30)
   if mo: scan("15")
   time.sleep(900)
  except KeyboardInterrupt: tg("⛔توقف"); break
  except Exception as e: log.error(f"err:{e}"); time.sleep(60)
if __name__=="__main__": main()
