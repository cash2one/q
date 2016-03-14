
if __name__ == "__main__":

    import sys; print sys.argv
    iss = "c" not in sys.argv
    isc = "s" not in sys.argv

    if iss and 0: 
        import profile; profile.install()

    from erpc import Server, Client
    
    host, port = "127.0.0.1", 10471

    import etcp

    if iss:
        d = {}
        class An(object):

            def get(self, key):
                return d.get(key, 0)

            def set(self, key, value):
                d[key] = value
                return value

        an = An()
        an.x = 0

        rs = Server(host, port)
        rs.add_service("an", an)
    
    if isc:
        nl = [0]

        import time
        begin = time.time()
        def on_resp(reqid, resp):
            # print resp
            nl[0] += 1
            if resp != nl[0]:
                print "err", resp, nl
            if nl[0] % 10000 == 0:
                print time.time(), nl, resp, resp / (time.time() - begin)
            # print "on_resp", reqid, resp

        rc = Client(host, port)

    n = 0
    while True:
        # if isc: reqid = rc.req("an", "ko", on_resp=on_resp)
        n += 1
        if isc: reqid = rc.req("an", "set", ("a", n),  on_resp=on_resp)
        etcp.poll()

# 1457957799.06 [750000] 750000 36304.2452634
# 1457957799.34 [760000] 760000 36304.550212
# 1457957799.61 [770000] 770000 36305.4484027
# 1457957799.89 [780000] 780000 36305.9851627
# 1457957800.16 [790000] 790000 36306.0930343
# 1457957800.44 [800000] 800000 36306.3451311
# 1457957800.71 [810000] 810000 36306.3058326
# 1457957800.99 [820000] 820000 36306.3077347
# 1457957801.27 [830000] 830000 36307.0100881
# 1457957801.54 [840000] 840000 36308.1743028
# 1457957801.81 [850000] 850000 36308.3778659
# 1457957802.09 [860000] 860000 36308.2327866
# 
