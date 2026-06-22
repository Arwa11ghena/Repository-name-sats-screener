import requests,logging
from datetime import datetime
import pytz
TELEGRAM_TOKEN="8690691652:AAETgCjYXYoY55VO9KVY8y-ISIRiAeU-_jc"
TELEGRAM_CHAT_ID="-1003742204870"
SYMBOLS=["2223","2170","2130","8230","2250","4146","2200","2070","6019","2222","1320","4325","2370","1810","1321","8030","1830","4300","2320","2190","1833","4090","2350","8010","4020","2083","4100","4220","4007","1120","1111","2081","2330","4322","4162","4194","7211","4050","2080","1831","2240","2150","4326","4260","4051","4015","1324","4292","8313","1835","2084","4262","7202","2270","1183","4006","2381","4191","4150","7203","6001","6016","1303","4170","4230","7204","4040","1834","4163","4002","1304","2290","6014","4160","2020","4261","2040","4011","1322","4145","2140","4061","6070","1323","2110","2230","1211","4142","4012","2090","2300","4161","1214","2281","2287","4291","4165","4263","2001","4323","2030","6018","2050","1302","2160","4021","4008","1301","4009","4290","1202","4327","4265","4004","7200","4071","1212","3007","2340","7040","4018","6004","4019","4147","4200","4193","4005","4240","6017","4031"]
logging.basicConfig(level=logging.INFO,format='%(asctime)s|%(message)s',datefmt='%H:%M:%S')
log=logging.getLogger(__name__)
RIYADH=pytz.timezone("Asia/Riyadh")
def now_r(): return datetime.now(RIYADH)
def is_market_open():
 n=now_r()
 if n.weekday()>=4: return False
 t=n.hour*60+n.minute
 return 9*60+30<=t<=15*60+30
def is_daily_time():
 n=now_r()
 if n.weekday()>=4: return False
 t=n.hour*60+n.minute
 return 16*60<=t<=16*60+20
def send_tg(msg):
 try:
  r=requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",json={"chat_id":TELEGRAM_CHAT_ID,"text":msg,"parse_mode":"HTML"},timeout=15)
  return r.status_code==200
 except Exception as e: log.error(f"TG:{e}"); return False
def fetch(sym,interval="1d",range_="10d"):
 try:
  url=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.SR"
  h={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
  r=requests.get(url,headers=h,params={"interval":interval,"range":range_},timeout=15)
  if r.status_code!=200: return None
  res=r.json().get("chart",{}).get("result",[])
  if not res: return None
  q=res[0].get("indicators",{}).get("quote",[{}])[0]
  C=q.get("close",[]); O=q.get("open",[]); H=q.get("high",[]); L=q.get("low",[]); V=q.get("volume",[])
  valid=[(o,h2,l,c,v) for o,h2,l,c,v in zip(O,H,L,C,V) if c and o]
  if len(valid)<3: return None
  c0=valid[-1][3]; c1=valid[-2][3]; c2=valid[-3][3]
  h0=valid[-1][1]; l0=valid[-1][2]
  v0=valid[-1][4] or 0; v1=valid[-2][4] or 0
  chg=(c0-c1)/c1*100 if c1 else 0
  rsi=50.0
  if len(valid)>=15:
   g=[]; ls=[]
   for i in range(-14,0):
    d=valid[i][3]-valid[i-1][3]
    (g if d>0 else ls).append(abs(d))
   ag=sum(g)/14 if g else 0; al=sum(ls)/14 if ls else 0
   rsi=100-100/(1+ag/al) if al>0 else (100 if ag>0 else 50)
  atr=abs(h0-l0) or c0*0.01
  vr=v0/v1 if v1>0 else 1
  return {"c":c0,"c1":c1,"c2":c2,"atr":atr,"rsi":rsi,"chg":chg,"vr":vr}
 except Exception as e: log.debug(f"{sym}:{e}"); return None
def signal(d,strict=False):
 c=d["c"]; c1=d["c1"]; c2=d["c2"]
 rsi=d["rsi"]; vr=d["vr"]; chg=d["chg"]; atr=d["atr"]
 min_chg=0.5 if strict else 0.3
 buy=c>c1 and c1>c2 and rsi<65 and vr>1.0 and chg>min_chg
 if not buy: return None
 sl_dist=atr*1.5
 return {"c":c,"sl":c-sl_dist,"t1":c+sl_dist,"t2":c+sl_dist*2,"t3":c+sl_dist*3,"rsi":rsi,"chg":chg,"vr":vr}
def fmt(buys,ok,lbl,now_str):
 msg=f"🔍 <b>SATS | {lbl}</b>\n⏰{now_str}\n━━━━━━━━━━━━━━━━\n\n📈 <b>شراء ({len(buys)})</b>\n\n"
 for sym,s in sorted(buys,key=lambda x:-x[1]["chg"]):
  msg+=f"🟢 <b>{sym}</b>\n💰 {s['c']:.2f} ▲{s['chg']:.1f}%\n🛑 SL: {s['sl']:.2f}\n🎯 TP1: {s['t1']:.2f} | TP2: {s['t2']:.2f} | TP3: {s['t3']:.2f}\n📊 RSI: {s['rsi']:.0f} | حجم: {s['vr']:.1f}x\n\n"
 msg+=f"━━━━━━━━━━━━━━━━\n📋 {ok}/{len(SYMBOLS)} سهم | SATS v3"
 return msg
def scan(interval,range_,lbl,strict):
 now_str=now_r().strftime("%Y-%m-%d %H:%M")
 ok=0; buys=[]
 for sym in SYMBOLS:
  d=fetch(sym,interval,range_)
  if not d: continue
  ok+=1
  s=signal(d,strict)
  if s: buys.append((sym,s))
 log.info(f"{lbl}|{ok}سهم|{len(buys)}إشارة")
 if buys: send_tg(fmt(buys,ok,lbl,now_str))
 else: send_tg(f"📋 <b>{lbl}</b> | {now_str}\n💤 لا إشارات\n📊 {ok}/{len(SYMBOLS)} سهم")
def main():
 now_str=now_r().strftime("%Y-%m-%d %H:%M")
 log.info(f"SATS|{now_str}")
 if is_market_open():
  log.info("مسح 15 دقيقة")
  scan("15m","1d","15 دقيقة ⚡",False)
 elif is_daily_time():
  log.info("مسح يومي")
  scan("1d","10d","يومي 📅",True)
 else:
  n=now_r()
  log.info(f"خارج وقت التداول {n.strftime('%H:%M')}")
main()
