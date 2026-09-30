#!/usr/bin/env python3
"""Durable Stage-1 auction triage.

Reads auctions/<id>/lots.json and live.json, merges by lot number, and writes
stage1-screen.csv. Cheapness never creates relevance; it only improves an
already relevant lot. Deep/photo research belongs in later stages.
"""
import csv, json, re, sys
from pathlib import Path

GROUPS={
"farm":["tractor","farm","plow","cultivator","seeder","livestock","horse","cattle","dairy","milking","fence","fencing","post hole","pitchfork","hay","load binder"],
"shop":["tool","saw","drill","grinder","welder","welding","vise","clamp","wrench","socket","jack","compressor","sander","lathe","mill","puller","hardware","fastener","extension cord"],
"auto":["automotive","trailer","hitch","tow","towing","battery charger","jumper","tire","lug","grease gun","gas can","motor","engine"],
"property":["ladder","shelving","cabinet","storage","plumbing","electrical","wire","pipe","hose","vac","freezer","washer","air conditioner","heater","mower","weed","sprayer","garden","shovel","rake"],
"value":["dewalt","makita","milwaukee","craftsman","estwing","speed queen","dyson","white's","selmer","fostoria","uranium","john deere","farmall","fairbanks morse","dietz","snap-on","skil"],
}
LOW=["figurine","doll","salt & pepper","plate","china","ornament","stuffed","costume jewelry"]
VAGUE=["bonus","assorted","misc","unknown","lot of"]

def classify(lot, live):
    cats=" ".join((c.get("fullCategory") or c.get("categoryName") or "") for c in lot.get("category",[]))
    text=(" ".join([lot.get("title",""),lot.get("description",""),cats])).lower()
    base=0; reasons=[]
    for group,keys in GROUPS.items():
        n=sum(k in text for k in keys)
        if n: reasons.append(group)
        base += n*(2 if group=="value" else 3)
    base -= 2*sum(k in text for k in LOW)
    bid=(live or {}).get("highBid",lot.get("current_bid",0)) or 0
    score=base + (1 if bid==0 and base>0 else 0) + (1 if lot.get("photo_count",0)>=4 and base>0 else 0)
    anomaly=any(k in text for k in VAGUE) and (lot.get("photo_count",0)>=3 or base>0)
    cls="STRONG TARGET" if score>=9 else "GOOD OPPORTUNITY" if score>=6 else "PRICE-DEPENDENT" if score>=3 else "REVIEW" if anomaly else "IGNORE"
    if sum(k in text for k in LOW)>=2 and score<6: cls="IGNORE"
    return score,cls,"|".join(reasons),"yes" if anomaly else ""

def main(aid):
    root=Path("auctions")/aid
    catalog=json.loads((root/"lots.json").read_text())["lots"]
    live_doc=json.loads((root/"live.json").read_text()); live=live_doc["lots"]
    lm={str(x["lotNumber"]):x for x in live}; rows=[]; seen=set()
    for entry,lot in enumerate(catalog,1):
        no=str(lot["lot_number"]); seen.add(no); lv=lm.get(no); score,cls,reasons,anom=classify(lot,lv)
        rows.append([entry,no,lot.get("id"),lot.get("title") or (lv or {}).get("title",""),lot.get("description",""),lot.get("photo_count",0),(lv or {}).get("highBid",lot.get("current_bid",0)),(lv or {}).get("bidCount",lot.get("bid_count",0)),(lv or {}).get("nextBid",lot.get("min_bid",0)),(lv or {}).get("status",lot.get("status","")),score,cls,reasons,anom,(lv or {}).get("lotUrl",lot.get("lot_url",""))])
    for lv in live:
        no=str(lv["lotNumber"])
        if no in seen: continue
        pseudo={"title":lv.get("title",""),"description":"","category":[],"photo_count":0,"current_bid":lv.get("highBid",0)}
        score,cls,reasons,anom=classify(pseudo,lv)
        rows.append(["LIVE_ONLY",no,lv.get("hibidLotId"),lv.get("title",""),"",0,lv.get("highBid",0),lv.get("bidCount",0),lv.get("nextBid",0),lv.get("status",""),score,cls,reasons,anom,lv.get("lotUrl","")])
    hdr=["entry","lot","id","title","description","photo_count","current_bid","bid_count","next_bid","status","score","classification","reasons","anomaly_review","lot_url"]
    with (root/"stage1-screen.csv").open("w",newline="") as f:
        w=csv.writer(f); w.writerow(hdr); w.writerows(rows)
    print(f"screened {len(rows)} records; advanced {sum(r[11] != 'IGNORE' for r in rows)}")

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: screen_auction.py AUCTION_ID")
    main(sys.argv[1])
