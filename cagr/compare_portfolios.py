aaa = """BSE
SUZLON
FACT
ITI
APARINDS
MAZDOCK
KALYANKJIL
OLECTRA
RECLTD
IRFC
WELCORP"""
# print(set(aaa.split("\n")))
# print(len(set(aaa.split("\n"))))

old = {'APARINDS', 'VBL', 'BSE', 'LINDEINDIA', 'RAYMOND', 'ENGINERSIN', 'EQUITASBNK', 'UNIONBANK', 'OLECTRA', 'TRITURBINE', 'JBMA', 'JSL', 'UCOBANK', 'SUZLON', 'KARURVYSYA', 'FINCABLES', 'FACT', 'IDFC', 'RAINBOW', 'ZENSARTECH', 'NCC', 'CGPOWER', 'IDFCFIRSTB', 'GESHIP', 'ITI', 'PFC', 'WELCORP', 'HAL', 'IRFC', 'RVNL', 'INDIANB', 'KALYANKJIL', 'MAZDOCK', 'MAHINDCIE', 'RECLTD'}

new = set(aaa.split("\n"))

print(old.intersection(new))
print(len(old.intersection(new)))

print(new.difference(old))
print(len(new.difference(old)))

print(old.difference(new))
print(len(old.difference(new)))

print(new.union(old))
print(len(new.union(old)))
