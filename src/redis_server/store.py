import threading
import time


class database:
    DATA = {}
    DATABASES = [{} for x in range(16)]
    TTL = {}
    LOCK = threading.Lock()
    CONFIG = {"databases": "16"}

    @staticmethod
    def select(db_index):
        if database.LOCK.acquire():
            database.DATA = database.DATABASES[int(db_index)]
            database.LOCK.release()

    @staticmethod
    def set(key, value):
        if database.LOCK.acquire():
            database.DATA[key] = value
            database.LOCK.release()

    @staticmethod
    def get(key):
        return database.DATA.get(key, None)

    @staticmethod
    def DEL(keys):
        ret = 0
        if database.LOCK.acquire():
            for key in keys:
                if database.DATA.get(key):
                    del database.DATA[key]
                    ret += 1
        database.LOCK.release()
        return ret

    @staticmethod
    def keys(key):
        import re
        patten = re.compile(key.replace("*", r"[\w]*").replace("?", "[\w]"))
        ret = filter(lambda x: patten.match(x), database.DATA.keys())
        return ret

    @staticmethod
    def get_type(key):
        return "string"

    @staticmethod
    def get_config(key):
        return [key, database.CONFIG.get(key, None)]

    @staticmethod
    def set_config(key, value):
        database.CONFIG[key] = value
        return "OK"

    @staticmethod
    def get_ttl(key):
        if database.get(key) is None:
            return -2
        ttl = database.TTL.get(key)
        if ttl:
            ttl = ttl - time.time()
            return int(ttl)
        return -1

    @staticmethod
    def get_pttl(key):
        if database.get(key) is None:
            return -2
        ttl = database.TTL.get(key)
        if ttl:
            ttl = ttl - time.time()
            return int(ttl * 1000)
        return -1

    @staticmethod
    def expire(key, ttl):
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA:
                database.TTL[key] = time.time() + int(ttl)
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def pexpire(key, ttl):
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA:
                database.TTL[key] = time.time() + float(ttl)/1000
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def expireat(key, ttl_time):
        ttl_time = float(ttl_time)
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA and time.time() < ttl_time:
                database.TTL[key] = ttl_time
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def pexpireat(key, ttl_time):
        ttl_time = float(ttl_time) / 1000
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA and time.time() < ttl_time:
                database.TTL[key] = ttl_time
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def persist(key):
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA and key in database.TTL:
                del database.TTL[key]
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def move(key, db_index):
        ret = 1
        if database.LOCK.acquire():
            if key in database.DATA:
                database.DATABASES[int(db_index)][key] = database.DATA.pop(key)
            else:
                ret = 0
        database.LOCK.release()
        return ret

    @staticmethod
    def randomkey():
        import random
        keys = database.DATA.keys()
        if keys:
            ret = keys[random.randint(0, len(keys))]
            return ret
        else:
            return None

    @staticmethod
    def rename(key, newkey):
        ret = "OK"
        if database.LOCK.acquire():
            if key in database.DATA:
                database.DATA[newkey] = database.DATA.pop(key)
                if key in database.TTL:
                    database.TTL[newkey] = database.TTL.pop(key)
            else:
                ret = "-ERR no such key"
        database.LOCK.release()
        return ret

    @staticmethod
    def renamenx(key, newkey):
        ret = 0
        if database.LOCK.acquire():
            if key in database.DATA and newkey not in database.DATA:
                database.DATA[newkey] = database.DATA.pop(key)
                if key in database.TTL:
                    database.TTL[newkey] = database.TTL.pop(key)
            else:
                ret = 1
        database.LOCK.release()
        return ret

    @staticmethod
    def dump(key):
        ret = database.get(key)
        if ret:
            import pickle
            return pickle.dumps(ret)
        return ret

    @staticmethod
    def restore(key, ttl, serialized_value):
        ret = "OK"
        import pickle
        if database.LOCK.acquire():
            try:
                value = pickle.loads(serialized_value)
                database.DATA[key] = value
                ttl = int(ttl)
                if ttl:
                    database.expire(key, ttl)
            except:
                ret = "-ERR DUMP payload version or checksum are wrong"
        database.LOCK.release()
        return ret


def ttl_thread():
    while True:
        time.sleep(1)
        now = time.time()
        keys = database.TTL.keys()
        keys_to_del = []
        for key in keys:
            if now - database.TTL[key] >= 0:
                del database.TTL[key]
                keys_to_del.append(key)
        database.DEL(keys_to_del)


# initial code
TTL_THREAD = threading.Thread(target=ttl_thread)
TTL_THREAD.start()
database.DATA = database.DATABASES[0]