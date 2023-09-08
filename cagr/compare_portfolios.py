aaa = """APARINDS
FACT
MAZDOCK
ZENSARTECH
RECLTD
SUZLON
OLECTRA
BSE
RVNL
IRFC
JSL"""
# print(set(aaa.split("\n")))
# print(len(set(aaa.split("\n"))))

old = {'KALYANKJIL', 'OLECTRA', 'LINDEINDIA', 'IDFCFIRSTB', 'SUZLON', 'PFC', 'JBMA', 'RAINBOW', 'UCOBANK', 'MAZDOCK', 'VBL', 'INDIANB', 'MAHINDCIE', 'IDFC', 'CGPOWER', 'RVNL', 'JSL', 'RAYMOND', 'ENGINERSIN', 'FACT', 'RECLTD', 'FINCABLES', 'EQUITASBNK', 'HAL', 'GESHIP', 'UNIONBANK', 'KARURVYSYA', 'ZENSARTECH', 'NCC', 'TRITURBINE', 'APARINDS'}

new = set(aaa.split("\n"))

print(old.intersection(new))
print(len(old.intersection(new)))

print(new.difference(old))
print(len(new.difference(old)))

print(old.difference(new))
print(len(old.difference(new)))

print(new.union(old))
print(len(new.union(old)))
