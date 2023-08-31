aaa = """APARINDS
FACT
JSL
SUZLON
OLECTRA
RECLTD
ZENSARTECH
KALYANKJIL
NCC
MAZDOCK
LINDEINDIA"""
# print(set(aaa.split("\n")))
# print(len(set(aaa.split("\n"))))

old = {'NCC', 'TRITURBINE', 'VBL', 'FINCABLES', 'JBMA', 'SUZLON', 'IDFCFIRSTB', 'OLECTRA', 'PFC', 'ENGINERSIN', 'ZENSARTECH', 'UNIONBANK', 'JSL', 'EQUITASBNK', 'UCOBANK', 'KARURVYSYA', 'RAYMOND', 'INDIANB', 'FACT', 'RAINBOW', 'RVNL', 'GESHIP', 'IDFC', 'KALYANKJIL', 'CGPOWER', 'MAHINDCIE', 'MAZDOCK', 'HAL'}

new = {'MAZDOCK', 'SUZLON', 'KALYANKJIL', 'JSL', 'APARINDS', 'LINDEINDIA', 'OLECTRA', 'NCC', 'ZENSARTECH', 'FACT', 'RECLTD'}

print(old.intersection(new))
print(len(old.intersection(new)))

print(new.difference(old))
print(len(new.difference(old)))

print(old.difference(new))
print(len(old.difference(new)))

print(new.union(old))
print(len(new.union(old)))
