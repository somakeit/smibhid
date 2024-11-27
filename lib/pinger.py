#Adapted from https://gist.github.com/shawwwn/91cc8979e33e82af6d99ec34c38195fb

from lib.ulogging import uLogger
from lib.module_config import ModuleConfig
from config import PINGER_WATCHDOG_IP, PINGER_WATCHDOG_INTERVAL_SECONDS, PINGER_WATCHDOG_RETRY_COUNT, PINGER_WATCHDOG_RELAY_PIN, PINGER_WATCHDOG_RELAY_ACTIVE_HIGH
from asyncio import sleep_ms, get_event_loop
from machine import Pin

class Pinger:
    def __init__(self, module_config: ModuleConfig, hid: object):
        self.log = uLogger("Pinger")
        if PINGER_WATCHDOG_IP:
            self.relay = Pin(PINGER_WATCHDOG_RELAY_PIN, Pin.OUT)
            self.relay_active_high = PINGER_WATCHDOG_RELAY_ACTIVE_HIGH
            self.relay.value(self.relay_active_high)
            self.hid = hid
            self.wifi = module_config.get_wifi()
            self.module_config = module_config
            self.interval = PINGER_WATCHDOG_INTERVAL_SECONDS
            self.retry_count = PINGER_WATCHDOG_RETRY_COUNT
            self.ip = PINGER_WATCHDOG_IP
            self.retries = 0
            self.loop = get_event_loop()
            self.log.info("Pinger initialised")
            self.loop.create_task(self.watchdog())
            self.relay_off = not self.relay_active_high
            self.relay_on = self.relay_active_high

    async def watchdog(self):
        self.log.info("Starting pinger")
        while not self.wifi.is_connected():
            self.log.info("Waiting for wifi to connect")
            await sleep_ms(5000)
        while True:
            try:
                pings = await self.async_ping(self.ip, count=self.retry_count)
                if pings[1] == 0:
                    self.log.warn(f"Failed to ping {self.ip} {self.retry_count} times")
                    self.log.info(f"Relay switching to {self.relay_off}")
                    self.relay.value(self.relay_off)
                    await sleep_ms(5000)
                    self.log.info(f"Relay switching to {self.relay_on}")
                    self.relay.value(self.relay_on)
                    self.log.warn("Ping watchdog restarted relay")
                else:
                    self.log.info(f"Pinged {self.ip} successfully {pings[1]} times")
            except Exception as e:
                self.log.error(f"Failed to ping {self.ip}: {e} - Relay kept {self.relay_active_high}")
            
            await sleep_ms(self.interval * 1000)
            

    def checksum(self, data):
        if len(data) & 0x1: # Odd number of bytes
            data += b'\0'
        cs = 0
        for pos in range(0, len(data), 2):
            b1 = data[pos]
            b2 = data[pos + 1]
            cs += (b1 << 8) + b2
        while cs >= 0x10000:
            cs = (cs & 0xffff) + (cs >> 16)
        cs = ~cs & 0xffff
        return cs

    async def async_ping(self, host, count=4, timeout=5000, interval=10, quiet=True, size=64):
        import utime
        import uselect
        import uctypes
        import usocket
        import ustruct
        import urandom

        # prepare packet
        assert size >= 16, "pkt size too small"
        pkt = b'Q'*size
        pkt_desc = {
            "type": uctypes.UINT8 | 0,
            "code": uctypes.UINT8 | 1,
            "checksum": uctypes.UINT16 | 2,
            "id": uctypes.UINT16 | 4,
            "seq": uctypes.INT16 | 6,
            "timestamp": uctypes.UINT64 | 8,
        } # packet header descriptor
        h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
        h.type = 8 # ICMP_ECHO_REQUEST
        h.code = 0
        h.checksum = 0
        h.id = urandom.getrandbits(16)
        h.seq = 1

        # init socket
        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_RAW, 1)
        sock.setblocking(0)
        sock.settimeout(timeout/1000)
        addr = usocket.getaddrinfo(host, 1)[0][-1][0] # ip address
        sock.connect((addr, 1))
        not quiet and print("PING %s (%s): %u data bytes" % (host, addr, len(pkt)))

        seqs = list(range(1, count+1)) # [1,2,...,count]
        c = 1
        t = 0
        n_trans = 0
        n_recv = 0
        finish = False
        while t < timeout:
            if t==interval and c<=count:
                # send packet
                h.checksum = 0
                h.seq = c
                h.timestamp = utime.ticks_us()
                h.checksum = self.checksum(pkt)
                if sock.send(pkt) == size:
                    n_trans += 1
                    t = 0 # reset timeout
                else:
                    seqs.remove(c)
                c += 1

            # recv packet
            while 1:
                socks, _, _ = uselect.select([sock], [], [], 0)
                if socks:
                    resp = socks[0].recv(4096)
                    resp_mv = memoryview(resp)
                    h2 = uctypes.struct(uctypes.addressof(resp_mv[20:]), pkt_desc, uctypes.BIG_ENDIAN)
                    # TODO: validate checksum (optional)
                    seq = h2.seq
                    if h2.type==0 and h2.id==h.id and (seq in seqs): # 0: ICMP_ECHO_REPLY
                        t_elasped = (utime.ticks_us()-h2.timestamp) / 1000
                        ttl = ustruct.unpack('!B', resp_mv[8:9])[0] # time-to-live
                        n_recv += 1
                        not quiet and print("%u bytes from %s: icmp_seq=%u, ttl=%u, time=%f ms" % (len(resp), addr, seq, ttl, t_elasped))
                        seqs.remove(seq)
                        if len(seqs) == 0:
                            finish = True
                            break
                else:
                    break

            if finish:
                break

            await sleep_ms(1)
            t += 1

        # close
        sock.close()
        ret = (n_trans, n_recv)
        not quiet and print("%u packets transmitted, %u packets received" % (n_trans, n_recv))
        return (n_trans, n_recv)
