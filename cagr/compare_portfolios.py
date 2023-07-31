aaa = """FACT
JBMA
RVNL
JSL
MAZDOCK
SUZLON
ZENSARTECH
PFC
ENGINERSIN
NCC
OLECTRA"""
# print(set(aaa.split("\n")))
# print(len(set(aaa.split("\n"))))

old = {
    "FACT",
    "FINCABLES",
    "UNIONBANK",
    "TRITURBINE",
    "EQUITASBNK",
    "CGPOWER",
    "HAL",
    "RAYMOND",
    "RAINBOW",
    "KARURVYSYA",
    "RVNL",
    "MAHINDCIE",
    "VBL",
    "NCC",
    "GESHIP",
    "INDIANB",
    "MAZDOCK",
    "KALYANKJIL",
    "JSL",
    "IDFCFIRSTB",
    "JBMA",
    "IDFC",
    "UCOBANK",
    "SUZLON",
}

new = {"MAZDOCK", "ENGINERSIN", "ZENSARTECH", "RVNL", "SUZLON", "JBMA", "FACT", "UCOBANK", "OLECTRA", "PFC", "JSL"}

print(old.intersection(new))
print(len(old.intersection(new)))

print(new.difference(old))
print(len(new.difference(old)))

print(old.difference(new))
print(len(old.difference(new)))

print(new.union(old))
print(len(new.union(old)))
