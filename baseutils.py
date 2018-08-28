dic32 = '0123456789ABCDEFGHIJKLMNOPQRSTUV'

def get_32(id):
    rem = list()
    while id > 0:
        rem.append(id % 32)
        id = id // 32
    rem.reverse()
    id32 = ''
    for i in rem:
        id32 += dic32[i]
    return id32

def get_10(id32):
    l = len(id32) - 1
    pos = 0
    id = 0
    for sym in id32:
        i = dic32.find(sym)
        id += i*(32**(l-pos))
        pos += 1
    return id