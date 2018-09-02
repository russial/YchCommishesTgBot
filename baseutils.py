dic32 = '0123456789ABCDEFGHIJKLMNOPQRSTUV'

def get_32(id: int) -> str:
    rem = list()
    while id > 0:
        rem.append(id % 32)
        id = id // 32
    rem.reverse()
    id32 = ''
    for i in rem:
        id32 += dic32[i]
    return id32

def get_10(id32: str) -> int:
    return int(id32, base=32)
