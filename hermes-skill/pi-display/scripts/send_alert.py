import json, os, sys, urllib.request

def send(payload):
    base=os.environ["HERMES_PI_URL"].rstrip("/"); token=os.environ["HERMES_PI_TOKEN"]
    data=json.dumps(payload).encode(); req=urllib.request.Request(base+"/v1/alerts",data=data,headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=3) as r: return json.loads(r.read())

if __name__ == "__main__": print(json.dumps(send(json.load(sys.stdin))))

